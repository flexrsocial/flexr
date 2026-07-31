package flexr.social.app.di

import android.content.Context
import androidx.room.Room
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import flexr.social.app.data.local.FlexrDatabase
import flexr.social.app.data.local.MatchDao
import flexr.social.app.data.local.MessageDao
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {

    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): FlexrDatabase =
        Room.databaseBuilder(context, FlexrDatabase::class.java, FlexrDatabase.NAME)
            // Der Inhalt ist reiner Cache des Servers — bei einem Schema-Wechsel
            // ist Neuaufbau günstiger als eine Migration.
            .fallbackToDestructiveMigration(dropAllTables = true)
            .build()

    @Provides
    fun provideMatchDao(database: FlexrDatabase): MatchDao = database.matchDao()

    @Provides
    fun provideMessageDao(database: FlexrDatabase): MessageDao = database.messageDao()
}
