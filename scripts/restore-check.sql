-- Pruefwerte fuer den Restore-Test, eine Zeile je Wert: <Bezeichnung>|<Wert>
-- (psql -At).
--
-- backup.sh ermittelt sie in derselben Transaktion, deren Snapshot pg_dump
-- sichert, und legt sie als restore-check.txt in den restic-Snapshot.
-- backup-verify.sh ermittelt sie erneut auf der Wiederherstellung und
-- vergleicht. Beide Seiten beschreiben so genau denselben Datenbankstand.
--
-- Bis 18.10.2026 verglich der Restore-Test gegen die Live-Datenbank, eine
-- knappe Stunde nach dem Backup. Er schlug an, sobald die App in der
-- Zwischenzeit schrieb (+2 Pushes, +2 E-Mails, -1 Nachricht), obwohl das
-- Backup einwandfrei war.

SELECT 'Tabellen', count(*)
  FROM information_schema.tables WHERE table_schema = 'public';

SELECT 'Aufzaehlungen', count(*)
  FROM pg_type t JOIN pg_namespace n ON n.oid = t.typnamespace
 WHERE t.typtype = 'e' AND n.nspname = 'public';

SELECT 'Fremdschluessel', count(*)
  FROM information_schema.table_constraints
 WHERE constraint_type = 'FOREIGN KEY' AND table_schema = 'public';

SELECT 'Migrationsstand', version_num FROM alembic_version;

-- Zeilenzahl je Tabelle. Faengt den Fall, dass das Schema vollstaendig ist,
-- die Daten aber fehlen.
--
-- Exakte Zaehlung ueber query_to_xml statt der Schaetzwerte aus
-- `pg_class.reltuples`: Schaetzwerte verlangen ein vorheriges ANALYZE, das als
-- nicht privilegierte Rolle ueber die Systemkataloge stolpert, und koennten
-- eine Abweichung verdecken. Bei der heutigen Datenmenge kostet die exakte
-- Zaehlung Millisekunden.
SELECT 'Zeilen ' || c.relname,
       (xpath(
          '/row/cnt/text()',
          query_to_xml(format('SELECT count(*) AS cnt FROM %I.%I', ns.nspname, c.relname),
                       false, true, '')
        ))[1]::text::bigint
  FROM pg_class c JOIN pg_namespace ns ON ns.oid = c.relnamespace
 WHERE ns.nspname = 'public' AND c.relkind = 'r'
 ORDER BY c.relname;
