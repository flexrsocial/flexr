# kotlinx.serialization: die generierten Serializer werden nur reflektiv über die
# @Serializable-Klassen erreicht — Companion + serializer() müssen bleiben.
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.**

-keepclassmembers class kotlinx.serialization.json.** {
    *** Companion;
}
-keepclasseswithmembers class kotlinx.serialization.json.** {
    kotlinx.serialization.KSerializer serializer(...);
}

-keep,includedescriptorclasses class flexr.social.app.**$$serializer { *; }
-keepclassmembers class flexr.social.app.** {
    *** Companion;
}
-keepclasseswithmembers class flexr.social.app.** {
    kotlinx.serialization.KSerializer serializer(...);
}

# Retrofit-Interfaces werden über Reflection instanziiert.
-keep,allowobfuscation,allowshrinking interface retrofit2.Call
-keep,allowobfuscation,allowshrinking class retrofit2.Response
-keep,allowobfuscation,allowshrinking class kotlin.coroutines.Continuation
