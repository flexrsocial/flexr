package flexr.social.app.ui.legal

import androidx.compose.animation.animateContentSize
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Remove
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import flexr.social.app.core.designsystem.icon.FlexrIcons
import flexr.social.app.core.designsystem.theme.FlexrTheme
import flexr.social.app.ui.navigation.LegalDocument

/**
 * Rechtstexte, nativ gesetzt. Tabellen scrollen bei Bedarf waagerecht in ihrem
 * eigenen Container, damit die Seite selbst nie seitlich verrutscht.
 */
@Composable
fun LegalScreen(
    document: LegalDocument,
    onBack: () -> Unit,
) {
    val page = remember(document) { LegalContent.of(document) }
    val colors = FlexrTheme.colors

    Column(Modifier.fillMaxSize().navigationBarsPadding()) {
        Row(
            Modifier.fillMaxWidth().padding(horizontal = 8.dp, vertical = 10.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            IconButton(onClick = onBack) {
                Icon(FlexrIcons.Back, contentDescription = "Zurück", tint = colors.chalk)
            }
            Text(
                text = document.title,
                style = MaterialTheme.typography.titleMedium,
                color = colors.chalk,
            )
        }
        Box(Modifier.fillMaxWidth().height(1.dp).background(colors.hairline))

        LazyColumn(
            modifier = Modifier.fillMaxSize().padding(horizontal = 20.dp),
            contentPadding = androidx.compose.foundation.layout.PaddingValues(
                top = 16.dp,
                bottom = 48.dp,
            ),
        ) {
            page.intro?.let { intro ->
                item {
                    Text(
                        text = intro,
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.chalkDim,
                        modifier = Modifier.padding(bottom = 20.dp),
                    )
                }
            }
            items(page.blocks.size) { index ->
                LegalBlockView(page.blocks[index])
            }
        }
    }
}

@Composable
private fun LegalBlockView(block: LegalBlock) {
    val colors = FlexrTheme.colors
    when (block) {
        is LegalBlock.Heading -> {
            Spacer(Modifier.height(24.dp))
            Text(
                text = block.text,
                style = MaterialTheme.typography.titleMedium,
                color = colors.chalk,
            )
            Spacer(Modifier.height(6.dp))
            Box(Modifier.fillMaxWidth().height(1.dp).background(colors.steel))
            Spacer(Modifier.height(10.dp))
        }

        is LegalBlock.Paragraph -> Text(
            text = block.text,
            style = MaterialTheme.typography.bodyMedium,
            color = colors.chalkDim,
            modifier = Modifier.padding(bottom = 8.dp),
        )

        is LegalBlock.Note -> Text(
            text = block.text,
            style = MaterialTheme.typography.bodySmall,
            color = colors.chalkDim,
            modifier = Modifier.padding(top = 8.dp, bottom = 8.dp),
        )

        is LegalBlock.Bullets -> Column(Modifier.padding(bottom = 8.dp)) {
            block.items.forEach { item ->
                Row(Modifier.padding(bottom = 8.dp)) {
                    Text("•", style = MaterialTheme.typography.bodyMedium, color = colors.plate)
                    Spacer(Modifier.width(10.dp))
                    Text(item, style = MaterialTheme.typography.bodyMedium, color = colors.chalkDim)
                }
            }
        }

        is LegalBlock.Lettered -> Column(Modifier.padding(bottom = 8.dp)) {
            block.items.forEachIndexed { index, item ->
                Row(Modifier.padding(bottom = 8.dp)) {
                    Text(
                        text = "${'a' + index})",
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.chalk,
                        fontWeight = FontWeight.SemiBold,
                    )
                    Spacer(Modifier.width(10.dp))
                    Text(item, style = MaterialTheme.typography.bodyMedium, color = colors.chalkDim)
                }
            }
        }

        is LegalBlock.KeyValues -> Column(Modifier.padding(bottom = 8.dp)) {
            block.rows.forEach { (key, value) ->
                Row(Modifier.fillMaxWidth().padding(bottom = 6.dp)) {
                    Text(
                        text = "$key:",
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.chalk,
                        modifier = Modifier.width(140.dp),
                    )
                    Text(value, style = MaterialTheme.typography.bodyMedium, color = colors.chalkDim)
                }
            }
        }

        is LegalBlock.Table -> Column(
            Modifier
                .fillMaxWidth()
                .padding(bottom = 12.dp)
                .horizontalScroll(rememberScrollState()),
        ) {
            Row(Modifier.padding(bottom = 6.dp)) {
                block.headers.forEach { header ->
                    Text(
                        text = header,
                        style = MaterialTheme.typography.titleSmall,
                        color = colors.chalkDim,
                        modifier = Modifier.width(TABLE_COLUMN_WIDTH.dp).padding(end = 10.dp),
                    )
                }
            }
            block.rows.forEach { row ->
                Box(Modifier.fillMaxWidth().height(1.dp).background(colors.steel))
                Row(Modifier.padding(vertical = 8.dp)) {
                    row.forEach { cell ->
                        Text(
                            text = cell,
                            style = MaterialTheme.typography.bodySmall,
                            color = colors.chalkDim,
                            modifier = Modifier.width(TABLE_COLUMN_WIDTH.dp).padding(end = 10.dp),
                        )
                    }
                }
            }
        }

        is LegalBlock.Faq -> {
            var expanded by remember { mutableStateOf(false) }
            Column(
                Modifier
                    .fillMaxWidth()
                    .padding(bottom = 12.dp)
                    .clip(MaterialTheme.shapes.medium)
                    .background(colors.surface2)
                    .border(
                        1.dp,
                        if (expanded) colors.plate.copy(alpha = 0.35f) else colors.hairline,
                        MaterialTheme.shapes.medium,
                    )
                    .clickable { expanded = !expanded }
                    .animateContentSize()
                    .padding(16.dp),
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = block.question,
                        style = MaterialTheme.typography.titleSmall,
                        color = colors.chalk,
                        modifier = Modifier.weight(1f),
                    )
                    Icon(
                        imageVector = if (expanded) Icons.Filled.Remove else Icons.Filled.Add,
                        contentDescription = null,
                        tint = colors.plate,
                        modifier = Modifier.size(20.dp),
                    )
                }
                if (expanded) {
                    Spacer(Modifier.height(10.dp))
                    Text(
                        text = block.answer,
                        style = MaterialTheme.typography.bodyMedium,
                        color = colors.chalkDim,
                    )
                }
            }
        }
    }
}

private const val TABLE_COLUMN_WIDTH = 200
