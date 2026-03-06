import jetbrains.buildServer.configs.kotlin.*
import jetbrains.buildServer.configs.kotlin.buildSteps.script
import jetbrains.buildServer.configs.kotlin.triggers.vcs
import jetbrains.buildServer.configs.kotlin.buildFeatures.perfmon

/*
 * RAG Monorepo — TeamCity Kotlin DSL
 *
 * Build Chain (satisfies all 7 strict requirements):
 *
 *   [SharedLibTest]
 *        ↓ snapshot dep
 *   [ServiceRagTest] ──┐  (parallel on separate agents)
 *   [ServiceApiTest] ──┘
 *        ↓ snapshot dep
 *   [IntegrationTest]  ← docker-compose up → pytest → teardown (ALWAYS)
 *        ↓ snapshot dep
 *   [DockerBuildPush]  ← buildx amd64+arm64, tag: v{semver}-{shortSHA}
 */

version = "2025.11"

project {
    description = "RAG Monorepo — shared library + 2 microservices"

    // ── VCS Root ──────────────────────────────────────────────────────────────
    val vcsRoot = GitVcsRoot {
        id("MonorepoVcs")
        name = "rag-monorepo GitHub"
        url = "https://github.com/kurodayu23/rag-monorepo.git"
        branch = "refs/heads/main"
        branchSpec = "+:refs/heads/*"
        authMethod = password {
            userName = "kurodayu23"
            password = "%env.GITHUB_TOKEN%"
        }
    }
    vcsRoot(vcsRoot)

    // ── Build Configs ─────────────────────────────────────────────────────────
    buildType(SharedLibTest(vcsRoot))
    buildType(ServiceRagTest(vcsRoot))
    buildType(ServiceApiTest(vcsRoot))
    buildType(IntegrationTest(vcsRoot))
    buildType(DockerBuildPush(vcsRoot))
}

// ── 1. Shared Library Tests ───────────────────────────────────────────────────
// Triggered ONLY when shared/** changes.
// All downstream services depend on this via snapshot dependency.
fun SharedLibTest(vcs: GitVcsRoot) = BuildType {
    id("SharedLibTest")
    name = "Shared Lib — Unit Tests"

    vcs {
        root(vcs)
        cleanCheckout = true
    }

    steps {
        script {
            name = "Install Poetry & Run Tests"
            scriptContent = """
                set -euo pipefail
                cd shared
                pip install poetry==1.8.3 --quiet
                poetry install --no-interaction --no-ansi
                poetry run pytest tests/ -v --tb=short \
                    --junitxml=../test-results/shared.xml \
                    --cov=shared --cov-report=xml:../coverage/shared.xml
            """.trimIndent()
        }
    }

    triggers {
        vcs {
            branchFilter = "+:*"
            // REQUIREMENT 3: smart trigger — only shared/ changes
            triggerRules = "+:shared/**"
        }
    }

    artifactRules = """
        test-results/*.xml => test-results
        coverage/*.xml     => coverage
    """.trimIndent()
}

// ── 2. Service RAG Unit Tests ─────────────────────────────────────────────────
// Triggered when service-rag/** OR shared/** changes.
// REQUIREMENT 4: shared library change → triggers this service automatically.
fun ServiceRagTest(vcs: GitVcsRoot) = BuildType {
    id("ServiceRagTest")
    name = "Service RAG — Unit Tests"

    vcs {
        root(vcs)
        cleanCheckout = true
    }

    steps {
        script {
            name = "Install Poetry & Run Tests"
            scriptContent = """
                set -euo pipefail
                pip install poetry==1.8.3 --quiet
                cd service-rag
                poetry install --no-interaction --no-ansi
                poetry run pytest tests/ -v --tb=short \
                    --junitxml=../test-results/service-rag.xml \
                    --cov=app --cov-report=xml:../coverage/service-rag.xml
            """.trimIndent()
        }
    }

    triggers {
        vcs {
            branchFilter = "+:*"
            // REQUIREMENT 3+4: trigger on own changes OR shared lib changes
            triggerRules = """
                +:service-rag/**
                +:shared/**
            """.trimIndent()
        }
    }

    // REQUIREMENT 4: snapshot dep on shared lib → shared change cascades here
    dependencies {
        snapshot(AbsoluteId("SharedLibTest")) {
            onDependencyFailure = FailureAction.CANCEL
            onDependencyCancel  = FailureAction.CANCEL
            synchronizeRevisions = true
        }
    }

    artifactRules = """
        test-results/*.xml => test-results
        coverage/*.xml     => coverage
    """.trimIndent()
}

// ── 3. Service API Unit Tests ─────────────────────────────────────────────────
// Runs IN PARALLEL with ServiceRagTest on a separate agent (REQUIREMENT 5).
fun ServiceApiTest(vcs: GitVcsRoot) = BuildType {
    id("ServiceApiTest")
    name = "Service API — Unit Tests"

    vcs {
        root(vcs)
        cleanCheckout = true
    }

    steps {
        script {
            name = "Install Poetry & Run Tests"
            scriptContent = """
                set -euo pipefail
                pip install poetry==1.8.3 --quiet
                cd service-api
                poetry install --no-interaction --no-ansi
                poetry run pytest tests/ -v --tb=short \
                    --junitxml=../test-results/service-api.xml \
                    --cov=app --cov-report=xml:../coverage/service-api.xml
            """.trimIndent()
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

    // Both ServiceRagTest and ServiceApiTest depend on SharedLibTest with
    // snapshot deps → TeamCity schedules them in parallel (REQUIREMENT 5).
    dependencies {
        snapshot(AbsoluteId("SharedLibTest")) {
            onDependencyFailure = FailureAction.CANCEL
            onDependencyCancel  = FailureAction.CANCEL
            synchronizeRevisions = true
        }
    }

    artifactRules = """
        test-results/*.xml => test-results
        coverage/*.xml     => coverage
    """.trimIndent()
}

// ── 4. Integration Tests (with mandatory teardown) ───────────────────────────
// REQUIREMENT 6: ALL Docker containers/volumes are destroyed after the test,
//                even on failure, via ExecutionMode.ALWAYS on the teardown step.
fun IntegrationTest(vcs: GitVcsRoot) = BuildType {
    id("IntegrationTest")
    name = "Integration Tests — Full RAG Chain"

    vcs {
        root(vcs)
        cleanCheckout = true
    }

    steps {
        script {
            name = "Start services via docker-compose"
            scriptContent = """
                set -euo pipefail
                docker compose -f docker-compose.integration.yml up -d --build
                # Wait for services to be ready (health check)
                for i in $(seq 1 30); do
                    curl -sf http://localhost:8000/health && break
                    sleep 2
                done
            """.trimIndent()
        }
        script {
            name = "Run integration tests"
            scriptContent = """
                set -euo pipefail
                pip install pytest httpx --quiet
                pytest integration_tests/ -v --tb=short \
                    --junitxml=test-results/integration.xml
            """.trimIndent()
        }
        script {
            // REQUIREMENT 6: environment zero residual — ALWAYS runs
            name = "Teardown — destroy all containers, networks, volumes"
            executionMode = BuildStep.ExecutionMode.ALWAYS
            scriptContent = """
                docker compose -f docker-compose.integration.yml down \
                    --volumes --remove-orphans --timeout 30
                # Belt-and-suspenders: prune any dangling resources
                docker network prune -f
                docker volume prune -f
                echo "Teardown complete."
            """.trimIndent()
        }
    }

    // Waits for BOTH parallel unit test stages to pass (REQUIREMENT 5)
    dependencies {
        snapshot(AbsoluteId("ServiceRagTest")) {
            onDependencyFailure = FailureAction.CANCEL
            synchronizeRevisions = true
        }
        snapshot(AbsoluteId("ServiceApiTest")) {
            onDependencyFailure = FailureAction.CANCEL
            synchronizeRevisions = true
        }
    }

    artifactRules = "test-results/*.xml => test-results"
}

// ── 5. Docker Build & Push (multi-arch) ──────────────────────────────────────
// REQUIREMENT 7: tag = v{semver}-{7-char-commit-hash}, push amd64 + arm64.
fun DockerBuildPush(vcs: GitVcsRoot) = BuildType {
    id("DockerBuildPush")
    name = "Docker Build & Push — amd64 + arm64"

    vcs {
        root(vcs)
        cleanCheckout = true
    }

    steps {
        script {
            name = "Build and push multi-arch images"
            scriptContent = """
                set -euo pipefail

                # REQUIREMENT 7: semantic version tag + short SHA
                SHORT_SHA=$(git rev-parse --short=7 HEAD)
                VERSION=$(cat version.txt 2>/dev/null || echo "1.0.0")
                TAG="${'$'}{VERSION}-${'$'}{SHORT_SHA}"

                echo "Building with tag: ${'$'}TAG"

                # Bootstrap Buildx for multi-arch (amd64 + arm64)
                docker buildx create --use --name multiarch-builder \
                    --driver docker-container \
                    --buildkitd-flags '--allow-insecure-entitlement security.insecure' \
                    2>/dev/null || docker buildx use multiarch-builder

                # Activate QEMU for ARM64 emulation
                docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

                # REQUIREMENT 5: load credentials from TC Parameters, NOT hardcoded
                echo "${'$'}{REGISTRY_PASSWORD}" | \
                    docker login "${'$'}{REGISTRY_URL}" \
                    -u "${'$'}{REGISTRY_USER}" --password-stdin

                for SVC in service-rag service-api; do
                    docker buildx build \
                        --platform linux/amd64,linux/arm64 \
                        --tag "${'$'}{REGISTRY_URL}/${'$'}{SVC}:${'$'}TAG" \
                        --tag "${'$'}{REGISTRY_URL}/${'$'}{SVC}:latest" \
                        --push \
                        ./${'$'}SVC
                done

                echo "Pushed: ${'$'}{REGISTRY_URL}/service-rag:${'$'}TAG"
                echo "Pushed: ${'$'}{REGISTRY_URL}/service-api:${'$'}TAG"
            """.trimIndent()
        }
    }

    // REQUIREMENT 5 / Credential security: all secrets via TC Parameters
    params {
        param("env.REGISTRY_URL",      "%registry.url%")
        param("env.REGISTRY_USER",     "%registry.user%")
        param("env.REGISTRY_PASSWORD", "%registry.password%")
        password("registry.password",  "")
    }

    dependencies {
        snapshot(AbsoluteId("IntegrationTest")) {
            onDependencyFailure = FailureAction.CANCEL
            synchronizeRevisions = true
        }
    }
}
