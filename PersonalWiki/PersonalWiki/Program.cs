namespace PersonalWiki;

internal static class Program
{
    /// <summary>
    /// Haupteinstiegspunkt der Anwendung.
    /// </summary>
    [STAThread]
    static void Main()
    {
        // Stellt High-DPI-Skalierung und Standard-Schriftart ein (.NET WinForms).
        ApplicationConfiguration.Initialize();

        // Gespeicherten Pfad zum Datenordner laden (falls vorhanden).
        AppConfig.Load();

        Application.Run(new MainForm());
    }
}
