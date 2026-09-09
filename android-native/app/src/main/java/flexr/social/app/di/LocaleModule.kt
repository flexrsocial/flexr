package flexr.social.app.di

import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import flexr.social.app.core.locale.AppStrings
import flexr.social.app.core.locale.ResourceAppStrings
import javax.inject.Singleton

/**
 * Bindet die Text-Schnittstelle an die Ressourcen-Umsetzung. Die Trennung
 * existiert wie bei [SessionModule] fuer die Tests.
 */
@Module
@InstallIn(SingletonComponent::class)
abstract class LocaleModule {

    @Binds
    @Singleton
    abstract fun bindAppStrings(impl: ResourceAppStrings): AppStrings
}
