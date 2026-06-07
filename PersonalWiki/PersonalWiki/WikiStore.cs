using System.IO;

namespace PersonalWiki;

/// <summary>
/// Kapselt alle Datei-Operationen des Wikis.
/// Speichermodell (bewusst einfach und migrationsfreundlich):
///   Datenordner/
///       Kategorie A/
///           Seite 1.md
///           Seite 2.md
///       Kategorie B/
///           Unterkategorie/
///               Seite 3.md
/// Jede Seite ist eine reine Markdown-Datei, jede Kategorie ein Ordner.
/// Dadurch ist beim Umzug bereits alles sortiert und menschenlesbar abgelegt.
/// </summary>
public class WikiStore
{
    public const string PageExtension = ".md";

    public string RootDirectory { get; }

    public WikiStore(string rootDirectory)
    {
        RootDirectory = rootDirectory;
        EnsureRoot();
    }

    /// <summary>Stellt sicher, dass der Datenordner existiert.</summary>
    public void EnsureRoot()
    {
        Directory.CreateDirectory(RootDirectory);
    }

    /// <summary>Liest den Inhalt einer Seite.</summary>
    public string ReadPage(string filePath) =>
        File.Exists(filePath) ? File.ReadAllText(filePath) : string.Empty;

    /// <summary>Schreibt den Inhalt einer Seite.</summary>
    public void WritePage(string filePath, string content) =>
        File.WriteAllText(filePath, content);

    /// <summary>Erstellt eine neue, leere Kategorie (Ordner).</summary>
    public string CreateCategory(string parentDirectory, string name)
    {
        var path = Path.Combine(parentDirectory, Sanitize(name));
        Directory.CreateDirectory(path);
        return path;
    }

    /// <summary>Erstellt eine neue Seite mit optionalem Startinhalt.</summary>
    public string CreatePage(string parentDirectory, string title)
    {
        Directory.CreateDirectory(parentDirectory);
        var fileName = Sanitize(title);
        if (!fileName.EndsWith(PageExtension, StringComparison.OrdinalIgnoreCase))
            fileName += PageExtension;

        var path = Path.Combine(parentDirectory, fileName);
        if (!File.Exists(path))
            File.WriteAllText(path, $"# {title}\n\n");
        return path;
    }

    /// <summary>
    /// Importiert eine bestehende Datei in eine Kategorie.
    /// Nicht-Markdown-Dateien werden als .md kopiert, damit sie im Wiki erscheinen.
    /// </summary>
    public string ImportFile(string sourceFile, string targetDirectory)
    {
        Directory.CreateDirectory(targetDirectory);
        var name = Path.GetFileNameWithoutExtension(sourceFile);
        var target = Path.Combine(targetDirectory, Sanitize(name) + PageExtension);

        // Bei Namenskonflikt eine Nummer anhängen.
        int counter = 1;
        while (File.Exists(target))
        {
            target = Path.Combine(targetDirectory, $"{Sanitize(name)} ({counter}){PageExtension}");
            counter++;
        }

        File.Copy(sourceFile, target);
        return target;
    }

    /// <summary>Benennt eine Seite oder Kategorie um.</summary>
    public string Rename(string path, string newName, bool isDirectory)
    {
        var parent = Path.GetDirectoryName(path) ?? RootDirectory;
        string target;

        if (isDirectory)
        {
            target = Path.Combine(parent, Sanitize(newName));
            Directory.Move(path, target);
        }
        else
        {
            var fileName = Sanitize(newName);
            if (!fileName.EndsWith(PageExtension, StringComparison.OrdinalIgnoreCase))
                fileName += PageExtension;
            target = Path.Combine(parent, fileName);
            File.Move(path, target);
        }

        return target;
    }

    /// <summary>Löscht eine Seite oder Kategorie (samt Inhalt).</summary>
    public void Delete(string path, bool isDirectory)
    {
        if (isDirectory)
        {
            if (Directory.Exists(path))
                Directory.Delete(path, recursive: true);
        }
        else
        {
            if (File.Exists(path))
                File.Delete(path);
        }
    }

    /// <summary>Entfernt für Dateinamen ungültige Zeichen.</summary>
    public static string Sanitize(string name)
    {
        name = name.Trim();
        foreach (var c in Path.GetInvalidFileNameChars())
            name = name.Replace(c, '_');
        return string.IsNullOrWhiteSpace(name) ? "Unbenannt" : name;
    }
}
