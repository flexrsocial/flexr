package flexr.social.app.data.local

import androidx.room.Database
import androidx.room.RoomDatabase
import androidx.room.TypeConverters

@Database(
    entities = [MatchEntity::class, MessageEntity::class],
    // 3: MatchEntity.isPremium (Premium-Abzeichen in der Match-/Chatliste).
    version = 3,
    exportSchema = false,
)
@TypeConverters(RoomConverters::class)
abstract class FlexrDatabase : RoomDatabase() {
    abstract fun matchDao(): MatchDao
    abstract fun messageDao(): MessageDao

    companion object {
        const val NAME = "flexr.db"
    }
}
