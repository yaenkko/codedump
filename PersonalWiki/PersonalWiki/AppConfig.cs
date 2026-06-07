using System.IO;

namespace PersonalWiki;

/// <summary>
/// Speichert und lädt den Pfad zum Wiki-Datenordner.
/// Die Konfiguration liegt als einfache Textdatei (wiki.config) neben der EXE,
/// damit das Programm portabel bleibt und nichts in der Registry hinterlässt.
/// </summary>
public static class AppConfig
{
    private static readonly string ConfigPath =
        Path.Combine(AppContext.BaseDirectory, "wiki.config");

    /// <summary>Aktueller Datenordner. Standard: Dokumente\PersonalWiki.</summary>
    public static string DataDirectory { get; private set; } = GetDefaultDirectory();

    private static string GetDefaultDirectory() =>
        Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
            "PersonalWiki");

    /// <summary>Lädt den gespeicherten Datenordner-Pfad, falls vorhanden.</summary>
    public static void Load()
    {
        try
        {
            if (File.Exists(ConfigPath))
            {
                var path = File.ReadAllText(ConfigPath).Trim();
                if (!string.IsNullOrWhiteSpace(path))
                    DataDirectory = path;
            }
        }
        catch
        {
            // Bei Fehlern bleibt der Standardordner aktiv.
        }
    }

    /// <summary>Setzt und speichert einen neuen Datenordner-Pfad.</summary>
    public static void Save(string directory)
    {
        DataDirectory = directory;
        try
        {
            File.WriteAllText(ConfigPath, directory);
        }
        catch
        {
            // Speichern der Konfiguration ist nicht kritisch.
        }
    }
}
