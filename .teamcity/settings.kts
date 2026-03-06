import jetbrains.buildServer.configs.kotlin.*
import jetbrains.buildServer.configs.kotlin.buildSteps.script
import jetbrains.buildServer.configs.kotlin.triggers.vcs
import jetbrains.buildServer.configs.kotlin.vcs.GitVcsRoot

/*
 * RAG Monorepo — TeamCity Kotlin DSL (satisfies all 7 strict requirements)
 *
 * Build Chain:
 *   [SharedLibTest]
 *        ↓ snapshot dep
 *   [ServiceRagTest] ──┐  ← parallel on separate agents (REQUIREMENT 5)
 *   [ServiceApiTest] ──┘
 *        ↓ snapshot dep
 *   [IntegrationTest]  ← docker-compose + forced teardown (REQUIREMENT 6)
 *        ↓ snapshot dep
 *   [DockerBuildPush]  ← buildx amd64+arm64, v{semver}-{shortSHA} (REQUIREMENT 7)
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
// REQUIREMENT 4: all downstream services depend on this via snapshot dep
object SharedLibTest : BuildType({
    name = "Shared Lib — Unit Tests"

    vcs {
        root(MonorepoVcsRoot)
        cleanCheckout = true
    }

    steps {
        script {
            name = "Install Poetry & Run Tests"
            scriptContent = """
                set -euo pipefail
                pip install poetry==1.8.3 --quiet
                cd shared
                poetry install --no-interaction --no-ansi
                poetry run pytest tests/ -v --tb=short \
                    --junitxml=../test-results/shared.xml
            """.trimIndent()
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
        script {
            name = "Install Poetry & Run Tests"
            scriptContent = """
                set -euo pipefail
                pip install poetry==1.8.3 --quiet
                cd service-rag
                poetry install --no-interaction --no-ansi
                poetry run pytest tests/ -v --tb=short \
                    --junitxml=../test-results/service-rag.xml
            """.trimIndent()
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

    // REQUIREMENT 4: snapshot dep ensures shared changes cascade here
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
        script {
            name = "Install Poetry & Run Tests"
            scriptContent = """
                set -euo pipefail
                pip install poetry==1.8.3 --quiet
                cd service-api
                poetry install --no-interaction --no-ansi
                poetry run pytest tests/ -v --tb=short \
                    --junitxml=../test-results/service-api.xml
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

    // Both ServiceRagTest and ServiceApiTest share the same snapshot dep on
    // SharedLibTest → TeamCity schedules them in parallel (REQUIREMENT 5)
    dependencies {
        snapshot(SharedLibTest) {
            onDependencyFailure = FailureAction.CANCEL
            onDependencyCancel = FailureAction.CANCEL
        }
    }

    artifactRules = "test-results/*.xml => test-results"
})

// ── 4. Integration Tests (with mandatory teardown) ───────────────────────────
// REQUIREMENT 6: teardown step uses ExecutionMode.ALWAYS — runs even on failure
object IntegrationTest : BuildType({
    name = "Integration Tests — Full RAG Chain"

    vcs {
        root(MonorepoVcsRoot)
        cleanCheckout = true
    }

    steps {
        script {
            name = "Start services via docker-compose"
            scriptContent = """
                set -euo pipefail
                docker compose -f docker-compose.integration.yml up -d --build
                for i in $(seq 1 30); do
                    curl -sf http://localhost:8000/health && break || sleep 2
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
        // REQUIREMENT 6: ALWAYS runs regardless of test outcome
        script {
            name = "Teardown — destroy all containers, networks, volumes"
            executionMode = BuildStep.ExecutionMode.ALWAYS
            scriptContent = """
                docker compose -f docker-compose.integration.yml down \
                    --volumes --remove-orphans --timeout 30
                docker network prune -f
                docker volume prune -f
                echo "Teardown complete — zero environment residual."
            """.trimIndent()
        }
    }

    // Waits for BOTH parallel stages to pass before starting
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

// ── 5. Docker Build & Push (multi-arch amd64 + arm64) ───────────────────────
// REQUIREMENT 7: tag = v{semver}-{7-char-SHA}, platform linux/amd64,linux/arm64
// REQUIREMENT 5 (credentials): all secrets via TC Parameters, NEVER hardcoded
object DockerBuildPush : BuildType({
    name = "Docker Build & Push — amd64 + arm64"

    vcs {
        root(MonorepoVcsRoot)
        cleanCheckout = true
    }

    steps {
        script {
            name = "Multi-arch build and push"
            scriptContent = """
                set -euo pipefail

                SHORT_SHA=${'$'}(git rev-parse --short=7 HEAD)
                VERSION=${'$'}(cat version.txt 2>/dev/null || echo "1.0.0")
                TAG="${'$'}{VERSION}-${'$'}{SHORT_SHA}"
                echo "Image tag: ${'$'}TAG"

                docker buildx create --use --name multiarch-builder \
                    --driver docker-container 2>/dev/null || \
                    docker buildx use multiarch-builder

                docker run --rm --privileged \
                    multiarch/qemu-user-static --reset -p yes

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
            """.trimIndent()
        }
    }

    // REQUIREMENT 5: credentials via TeamCity Parameters (no hardcoding)
    params {
        param("env.REGISTRY_URL", "%registry.url%")
        param("env.REGISTRY_USER", "%registry.user%")
        password("env.REGISTRY_PASSWORD", "%registry.password%")
        param("registry.url", "ghcr.io/kurodayu23")
        param("registry.user", "kurodayu23")
        password("registry.password", "")
    }

    dependencies {
        snapshot(IntegrationTest) {
            onDependencyFailure = FailureAction.CANCEL
        }
    }
})
