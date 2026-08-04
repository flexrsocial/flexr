package flexr.social.app.di

import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import flexr.social.app.data.session.DataStoreSessionStore
import flexr.social.app.data.session.SessionStore
import javax.inject.Singleton

/**
 * Bindet die Sitzungs-Schnittstelle an die DataStore-Umsetzung. Die Trennung
 * existiert für die Tests: [SessionStore] hängt sonst am Android-Context und
 * macht damit jedes Repository und jedes ViewModel darüber in reinen
 * JVM-Tests unkonstruierbar.
 */
@Module
@InstallIn(SingletonComponent::class)
abstract class SessionModule {

    @Binds
    @Singleton
    abstract fun bindSessionStore(impl: DataStoreSessionStore): SessionStore
}
