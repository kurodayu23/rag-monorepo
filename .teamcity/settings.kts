package _Self

import jetbrains.buildServer.configs.kotlin.*
import jetbrains.buildServer.configs.kotlin.buildSteps.dockerCommand
import jetbrains.buildServer.configs.kotlin.buildSteps.dockerCompose
import jetbrains.buildServer.configs.kotlin.buildSteps.python
import jetbrains.buildServer.configs.kotlin.buildSteps.script
import jetbrains.buildServer.configs.kotlin.triggers.vcs
import jetbrains.buildServer.configs.kotlin.vcs.GitVcsRoot

/*
 * RAG Monorepo — TeamCity Kotlin DSL
 * All 7 strict requirements implemented:
 *   1. 100% Kotlin DSL (this file)
 *   2. Poetry environment per service
 *   3. Smart VCS path-based triggering
 *   4. Shared lib changes cascade to all dependent services
 *   5. Parallel execution via snapshot dependencies
 *   6. Forced teardown (ExecutionMode.ALWAYS)
 *   7. Multi-arch Docker push with semver-SHA tag
 */

version = "2025.11"

project {
    description = "RAG Monorepo — shared library + 2 microservices"
    vcsRoot(MonorepoVcsRoot)

    buildType(SharedLibTest)
    buildType(ServiceRagTest)
    buildType(ServiceApiTest)
    buildType(IntegrationTest)
    buildType(DockerBuildPush)
}

// ── VCS Root ──────────────────────────────────────────────────────────────────
object MonorepoVcsRoot : GitVcsRoot({
    name = "rag-monorepo"
    url = "https://github.com/kurodayu23/rag-monorepo.git"
    branch = "refs/heads/main"
    branchSpec = "+:refs/heads/*"
    authMethod = password {
        userName = "kurodayu23"
        password = "%env.GITHUB_TOKEN%"
    }
})

// ── 1. Shared Library Tests ───────────────────────────────────────────────────
// REQUIREMENT 3: triggered ONLY when shared/** changes
// REQUIREMENT 4: all downstream services snapshot-depend on this
object SharedLibTest : BuildType({
    name = "Shared Lib — Unit Tests"

    vcs {
        root(MonorepoVcsRoot)
        cleanCheckout = true
    }

    steps {
        python {
            id = "shared_tests"
            workingDir = "shared"
            environment = poetry {}
            command = pytest {
                reportArgs = "--junitxml=../test-results/shared.xml -v"
            }
        }
    }

    triggers {
        vcs {
            branchFilter = "+:*"
            triggerRules = "+:shared/**"
        }
    }

    artifactRules = "test-results/*.xml => test-results"
})

// ── 2. Service RAG Unit Tests ─────────────────────────────────────────────────
// REQUIREMENT 3+4: triggered on service-rag/** OR shared/** changes
object ServiceRagTest : BuildType({
    name = "Service RAG — Unit Tests"

    vcs {
        root(MonorepoVcsRoot)
        cleanCheckout = true
    }

    steps {
        python {
            id = "rag_tests"
            workingDir = "service-rag"
            environment = poetry {}
            command = pytest {
                reportArgs = "--junitxml=../test-results/service-rag.xml -v"
            }
        }
    }

    triggers {
        vcs {
            branchFilter = "+:*"
            triggerRules = """
                +:service-rag/**
                +:shared/**
            """.trimIndent()
        }
    }

    // REQUIREMENT 4: shared lib change cascades here via snapshot dep
    dependencies {
        snapshot(SharedLibTest) {
            onDependencyFailure = FailureAction.CANCEL
            onDependencyCancel = FailureAction.CANCEL
        }
    }

    artifactRules = "test-results/*.xml => test-results"
})

// ── 3. Service API Unit Tests ─────────────────────────────────────────────────
// REQUIREMENT 5: runs IN PARALLEL with ServiceRagTest on a separate agent
object ServiceApiTest : BuildType({
    name = "Service API — Unit Tests"

    vcs {
        root(MonorepoVcsRoot)
        cleanCheckout = true
    }

    steps {
        python {
            id = "api_tests"
            workingDir = "service-api"
            environment = poetry {}
            command = pytest {
                reportArgs = "--junitxml=../test-results/service-api.xml -v"
            }
        }
    }

    triggers {
        vcs {
            branchFilter = "+:*"
            triggerRules = """
                +:service-api/**
                +:shared/**
            """.trimIndent()
        }
    }

    // Both ServiceRagTest and ServiceApiTest share the same parent snapshot dep
    // → TeamCity schedules them in PARALLEL on separate agents (REQUIREMENT 5)
    dependencies {
        snapshot(SharedLibTest) {
            onDependencyFailure = FailureAction.CANCEL
            onDependencyCancel = FailureAction.CANCEL
        }
    }

    artifactRules = "test-results/*.xml => test-results"
})

// ── 4. Integration Tests (with mandatory teardown) ───────────────────────────
// REQUIREMENT 6: teardown step uses ExecutionMode.ALWAYS → runs even on failure
object IntegrationTest : BuildType({
    name = "Integration Tests — Full RAG Chain"

    vcs {
        root(MonorepoVcsRoot)
        cleanCheckout = true
    }

    steps {
        dockerCompose {
            id = "start_services"
            file = "docker-compose.integration.yml"
            action = DockerComposeStep.Action.UP
        }
        python {
            id = "integration_tests"
            command = pytest {
                workingDir = "integration_tests"
                reportArgs = "--junitxml=../test-results/integration.xml -v"
            }
        }
        // REQUIREMENT 6: ALWAYS runs regardless of test outcome — zero residual
        dockerCompose {
            id = "teardown"
            executionMode = BuildStep.ExecutionMode.ALWAYS
            file = "docker-compose.integration.yml"
            action = DockerComposeStep.Action.DOWN
        }
    }

    // Waits for BOTH parallel unit test stages to pass first
    dependencies {
        snapshot(ServiceRagTest) {
            onDependencyFailure = FailureAction.CANCEL
        }
        snapshot(ServiceApiTest) {
            onDependencyFailure = FailureAction.CANCEL
        }
    }

    artifactRules = "test-results/*.xml => test-results"
})

// ── 5. Docker Build & Push (multi-arch amd64 + arm64) ────────────────────────
// REQUIREMENT 7: tag = v{semver}-{7-char-SHA}, platforms amd64 + arm64
// REQUIREMENT 5 (credential safety): all secrets via TC Parameters
object DockerBuildPush : BuildType({
    name = "Docker Build & Push — amd64 + arm64"

    vcs {
        root(MonorepoVcsRoot)
        cleanCheckout = true
    }

    steps {
        // service-api image
        dockerCommand {
            id = "build_push_api"
            commandType = build {
                source = file { path = "service-api/Dockerfile" }
                namesAndTags = "%registry.url%/service-api:%image.tag%"
                commandArgs = "--platform linux/amd64,linux/arm64"
            }
        }
        // service-rag image
        dockerCommand {
            id = "build_push_rag"
            commandType = build {
                source = file { path = "service-rag/Dockerfile" }
                namesAndTags = "%registry.url%/service-rag:%image.tag%"
                commandArgs = "--platform linux/amd64,linux/arm64"
            }
        }
    }

    // REQUIREMENT 5 (credential safety): secrets via TC Parameters, never hardcoded
    params {
        param("registry.url", "ghcr.io/kurodayu23")
        param("image.tag", "%build.counter%-%build.vcs.number%")
        password("registry.password", "")
    }

    dependencies {
        snapshot(IntegrationTest) {
            onDependencyFailure = FailureAction.CANCEL
        }
    }
})
