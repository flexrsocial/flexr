package flexr.social.app.di

import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import javax.inject.Qualifier
import javax.inject.Singleton
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob

/**
 * Lebensdauer der App, nicht eines Bildschirms. Fuer Sammler, die es geben
 * muss, solange der Prozess lebt — derzeit nur die Sprachwahl in
 * [flexr.social.app.core.locale.AppStrings].
 *
 * [SupervisorJob], damit ein Fehler in einem Sammler nicht die uebrigen
 * mitreisst.
 */
@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class ApplicationScope

@Module
@InstallIn(SingletonComponent::class)
object CoroutineModule {

    @Provides
    @Singleton
    @ApplicationScope
    fun provideApplicationScope(): CoroutineScope =
        CoroutineScope(SupervisorJob() + Dispatchers.Default)
}
