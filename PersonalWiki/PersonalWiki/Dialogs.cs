namespace PersonalWiki;

/// <summary>
/// Einfache Dialog-Hilfen. WinForms bringt keinen eingebauten Eingabedialog mit,
/// deshalb hier eine schlanke eigene Variante.
/// </summary>
public static class Dialogs
{
    /// <summary>
    /// Zeigt einen Eingabedialog. Gibt den eingegebenen Text zurück
    /// oder null, wenn abgebrochen wurde.
    /// </summary>
    public static string? Prompt(string title, string label, string defaultValue = "")
    {
        using var form = new Form
        {
            Text = title,
            Width = 420,
            Height = 170,
            FormBorderStyle = FormBorderStyle.FixedDialog,
            StartPosition = FormStartPosition.CenterParent,
            MaximizeBox = false,
            MinimizeBox = false
        };

        var lbl = new Label
        {
            Text = label,
            Left = 12,
            Top = 15,
            Width = 380,
            AutoSize = false
        };

        var input = new TextBox
        {
            Left = 12,
            Top = 40,
            Width = 380,
            Text = defaultValue
        };
        input.SelectAll();

        var ok = new Button
        {
            Text = "OK",
            DialogResult = DialogResult.OK,
            Left = 236,
            Top = 80,
            Width = 75
        };

        var cancel = new Button
        {
            Text = "Abbrechen",
            DialogResult = DialogResult.Cancel,
            Left = 317,
            Top = 80,
            Width = 75
        };

        form.Controls.Add(lbl);
        form.Controls.Add(input);
        form.Controls.Add(ok);
        form.Controls.Add(cancel);
        form.AcceptButton = ok;   // Enter = OK
        form.CancelButton = cancel; // Esc = Abbrechen

        var result = form.ShowDialog();
        if (result != DialogResult.OK)
            return null;

        var text = input.Text.Trim();
        return string.IsNullOrWhiteSpace(text) ? null : text;
    }
}
