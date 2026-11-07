package flexr.social.app.di

import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import flexr.social.app.data.restore.CredentialManagerRestoreClient
import flexr.social.app.data.restore.RestoreCredentialClient
import javax.inject.Singleton

/**
 * Bindet den Restore-Key-Zugriff an den Credential Manager - dieselbe Trennung
 * wie in [SessionModule]: [CredentialManagerRestoreClient] braucht einen
 * Context, der RestoreKeyManager darüber soll in JVM-Tests laufen.
 */
@Module
@InstallIn(SingletonComponent::class)
abstract class RestoreModule {

    @Binds
    @Singleton
    abstract fun bindRestoreCredentialClient(impl: CredentialManagerRestoreClient): RestoreCredentialClient
}
