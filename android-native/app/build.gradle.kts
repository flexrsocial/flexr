import java.util.Properties

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ksp)
    alias(libs.plugins.hilt)
}

/**
 * Release-Signing: wiederverwendet den bestehenden Upload-Key aus dem
 * TWA-Build (android/android.keystore), damit die Play-Store-App weiterhin
 * mit demselben Schlüssel aktualisiert werden kann. Passwort kommt aus
 * android/KEYSTORE-CREDENTIALS.txt (nicht im Git) oder aus -Pflexr.keystorePassword.
 */
val legacyKeystore = rootProject.file("../android/android.keystore")
val legacyCredentials = rootProject.file("../android/KEYSTORE-CREDENTIALS.txt")
val keystorePassword: String? = (findProperty("flexr.keystorePassword") as String?)
    ?: legacyCredentials.takeIf { it.isFile }
        ?.readLines()
        ?.firstOrNull { it.startsWith("Passwort (Store + Key):") }
        ?.substringAfter(": ")
        ?.trim()

android {
    namespace = "flexr.social.app"
    compileSdk = 36

    defaultConfig {
        applicationId = "flexr.social.app"
        minSdk = 26
        targetSdk = 36
        versionCode = 25
        versionName = "2.2.8"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        resourceConfigurations += listOf("de")
    }

    signingConfigs {
        if (legacyKeystore.isFile && keystorePassword != null) {
            create("release") {
                storeFile = legacyKeystore
                storePassword = keystorePassword
                keyAlias = "flexr"
                keyPassword = keystorePassword
            }
        }
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
            isMinifyEnabled = false
        }
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
            signingConfig = signingConfigs.findByName("release")
        }
    }

    buildFeatures {
        compose = true
        buildConfig = true
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
        isCoreLibraryDesugaringEnabled = false
    }

    kotlin {
        compilerOptions {
            jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
        }
    }

    packaging {
        resources {
            excludes += setOf(
                "/META-INF/{AL2.0,LGPL2.1}",
                "/META-INF/DEPENDENCIES",
                "/META-INF/LICENSE*",
            )
        }
    }

    /** API-Endpunkte pro Build-Typ — Debug kann gegen die lokale Testumgebung laufen. */
    flavorDimensions += "backend"
    productFlavors {
        create("prod") {
            dimension = "backend"
            buildConfigField("String", "API_BASE_URL", "\"https://flexr.social/\"")
        }
        create("local") {
            dimension = "backend"
            applicationIdSuffix = ".local"
            versionNameSuffix = "-local"
            // 10.0.2.2 = Host-Rechner aus Sicht des Android-Emulators
            buildConfigField("String", "API_BASE_URL", "\"http://10.0.2.2:8000/\"")
        }
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.core.splashscreen)
    implementation(libs.androidx.activity.compose)
    implementation(libs.androidx.browser)

    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.runtime.compose)
    implementation(libs.androidx.lifecycle.viewmodel.compose)

    implementation(platform(libs.compose.bom))
    implementation(libs.compose.ui)
    implementation(libs.compose.ui.graphics)
    implementation(libs.compose.ui.tooling.preview)
    implementation(libs.compose.material3)
    implementation(libs.compose.material.icons.extended)
    implementation(libs.compose.animation)
    implementation(libs.compose.foundation)
    debugImplementation(libs.compose.ui.tooling)

    implementation(libs.androidx.navigation.compose)

    implementation(libs.hilt.android)
    ksp(libs.hilt.compiler)
    implementation(libs.hilt.navigation.compose)
    implementation(libs.hilt.work)
    ksp(libs.hilt.ext.compiler)

    implementation(libs.room.runtime)
    implementation(libs.room.ktx)
    ksp(libs.room.compiler)

    implementation(libs.retrofit)
    implementation(libs.retrofit.serialization)
    implementation(libs.okhttp)
    implementation(libs.okhttp.logging)
    implementation(libs.kotlinx.serialization.json)

    implementation(libs.coil.compose)

    implementation(libs.camera.core)
    implementation(libs.camera.camera2)
    implementation(libs.camera.lifecycle)
    implementation(libs.camera.view)

    implementation(libs.androidx.datastore.preferences)
    implementation(libs.androidx.work.runtime)

    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
    testImplementation(libs.okhttp.mockwebserver)
    testImplementation(libs.turbine)
    androidTestImplementation(libs.androidx.test.junit)
    androidTestImplementation(libs.androidx.test.espresso)
}
