package flexr.social.app.di

import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent
import flexr.social.app.core.media.ImageProcessor
import flexr.social.app.core.media.PhotoPreparer
import javax.inject.Singleton

/**
 * Bindet die Bildaufbereitung an die Android-Umsetzung — dieselbe Trennung wie
 * in [SessionModule] und aus demselben Grund: [ImageProcessor] braucht einen
 * Context, ViewModels darüber wären sonst in reinen JVM-Tests nicht baubar.
 */
@Module
@InstallIn(SingletonComponent::class)
abstract class MediaModule {

    @Binds
    @Singleton
    abstract fun bindPhotoPreparer(impl: ImageProcessor): PhotoPreparer
}
