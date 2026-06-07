using System.IO;

namespace PersonalWiki;

/// <summary>
/// Hauptfenster des persönlichen Wikis.
/// Links: durchsuchbarer Baum aus Kategorien (Ordner) und Seiten (.md-Dateien).
/// Rechts: Editor zum Bearbeiten und eine umschaltbare HTML-Vorschau.
/// </summary>
public class MainForm : Form
{
    // Kleine Hilfsstruktur, die an jeden Baumknoten gehängt wird.
    private sealed record NodeInfo(string Path, bool IsDirectory);

    private WikiStore _store;

    private readonly TreeView _tree = new();
    private readonly TextBox _search = new();
    private readonly TextBox _editor = new();
    private readonly WebBrowser _preview = new();
    private readonly ToolStripStatusLabel _status = new();
    private readonly ToolStripButton _previewButton;
    private readonly SplitContainer _split = new() { Dock = DockStyle.Fill, FixedPanel = FixedPanel.Panel1 };

    private string? _currentFile;
    private bool _isDirty;
    private bool _previewMode;
    private bool _loadingPage;

    public MainForm()
    {
        _store = new WikiStore(AppConfig.DataDirectory);

        Text = "Personal Wiki";
        Width = 1100;
        Height = 700;
        StartPosition = FormStartPosition.CenterScreen;
        KeyPreview = true;
        MinimumSize = new Size(640, 420);

        // ---------- Werkzeugleiste ----------
        var toolbar = new ToolStrip { GripStyle = ToolStripGripStyle.Hidden };

        toolbar.Items.Add(MakeButton("Neue Kategorie", (_, _) => NewCategory()));
        toolbar.Items.Add(MakeButton("Neue Seite", (_, _) => NewPage()));
        toolbar.Items.Add(new ToolStripSeparator());
        toolbar.Items.Add(MakeButton("Speichern (Strg+S)", (_, _) => SaveCurrent(showStatus: true)));
        toolbar.Items.Add(MakeButton("Importieren…", (_, _) => ImportFiles()));
        toolbar.Items.Add(new ToolStripSeparator());
        toolbar.Items.Add(MakeButton("Umbenennen", (_, _) => RenameSelected()));
        toolbar.Items.Add(MakeButton("Löschen", (_, _) => DeleteSelected()));
        toolbar.Items.Add(new ToolStripSeparator());
        _previewButton = MakeButton("Vorschau", (_, _) => TogglePreview());
        _previewButton.CheckOnClick = true;
        toolbar.Items.Add(_previewButton);
        toolbar.Items.Add(new ToolStripSeparator());
        toolbar.Items.Add(MakeButton("Datenordner…", (_, _) => ChangeDataFolder()));

        // ---------- Statusleiste ----------
        var statusStrip = new StatusStrip();
        statusStrip.Items.Add(_status);

        // ---------- Linke Seite: Suche + Baum ----------
        _search.Dock = DockStyle.Top;
        _search.PlaceholderText = "Seiten durchsuchen…";
        _search.TextChanged += (_, _) => ReloadTree(_search.Text.Trim());

        _tree.Dock = DockStyle.Fill;
        _tree.HideSelection = false;
        _tree.AfterSelect += Tree_AfterSelect;
        _tree.ImageList = BuildIcons();

        var leftPanel = new Panel { Dock = DockStyle.Fill };
        leftPanel.Controls.Add(_tree);
        leftPanel.Controls.Add(_search);

        // ---------- Rechte Seite: Editor + Vorschau ----------
        _editor.Multiline = true;
        _editor.Dock = DockStyle.Fill;
        _editor.ScrollBars = ScrollBars.Vertical;
        _editor.AcceptsTab = true;
        _editor.WordWrap = true;
        _editor.Font = new Font("Consolas", 11f);
        _editor.HideSelection = false;
        _editor.TextChanged += Editor_TextChanged;

        _preview.Dock = DockStyle.Fill;
        _preview.Visible = false;
        _preview.ScriptErrorsSuppressed = true;
        _preview.AllowWebBrowserDrop = false;
        _preview.IsWebBrowserContextMenuEnabled = false;

        var rightPanel = new Panel { Dock = DockStyle.Fill };
        rightPanel.Controls.Add(_preview);
        rightPanel.Controls.Add(_editor);

        // ---------- Aufteilung ----------
        // SplitterDistance wird erst in OnShown gesetzt, wenn das Fenster
        // seine echte Größe hat (sonst droht eine Ausnahme).
        _split.Panel1.Controls.Add(leftPanel);
        _split.Panel2.Controls.Add(rightPanel);

        // Reihenfolge des Hinzufügens bestimmt das Andocken.
        Controls.Add(_split);
        Controls.Add(statusStrip);
        Controls.Add(toolbar);

        KeyDown += MainForm_KeyDown;
        FormClosing += (_, _) => SaveCurrent();

        ReloadTree();
        SetStatus($"Datenordner: {_store.RootDirectory}");
    }

    protected override void OnShown(EventArgs e)
    {
        base.OnShown(e);
        // Jetzt hat der SplitContainer seine endgültige Breite.
        try { _split.SplitterDistance = 300; } catch { /* zu schmales Fenster */ }
    }

    // ----------------------------------------------------------------- UI-Helfer

    private static ToolStripButton MakeButton(string text, EventHandler onClick)
    {
        var btn = new ToolStripButton(text) { DisplayStyle = ToolStripItemDisplayStyle.Text };
        btn.Click += onClick;
        return btn;
    }

    private static ImageList BuildIcons()
    {
        var images = new ImageList { ImageSize = new Size(16, 16), ColorDepth = ColorDepth.Depth32Bit };
        images.Images.Add("folder", MakeIcon(Color.Goldenrod));
        images.Images.Add("page", MakeIcon(Color.SteelBlue));
        return images;
    }

    private static Bitmap MakeIcon(Color color)
    {
        var bmp = new Bitmap(16, 16);
        using var g = Graphics.FromImage(bmp);
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
        using var brush = new SolidBrush(color);
        g.FillRectangle(brush, 3, 3, 10, 10);
        return bmp;
    }

    private void SetStatus(string text) => _status.Text = text;

    // ----------------------------------------------------------------- Baum

    private void ReloadTree(string filter = "")
    {
        _tree.BeginUpdate();
        _tree.Nodes.Clear();

        try
        {
            _store.EnsureRoot();

            foreach (var dir in Directory.GetDirectories(_store.RootDirectory).OrderBy(p => p))
            {
                var node = BuildDirectoryNode(dir, filter);
                if (node != null) _tree.Nodes.Add(node);
            }
            foreach (var file in Directory.GetFiles(_store.RootDirectory, "*" + WikiStore.PageExtension).OrderBy(p => p))
            {
                var fileNode = BuildFileNode(file, filter);
                if (fileNode != null) _tree.Nodes.Add(fileNode);
            }

            if (filter.Length > 0)
                _tree.ExpandAll();
        }
        catch (Exception ex)
        {
            SetStatus("Fehler beim Laden: " + ex.Message);
        }
        finally
        {
            _tree.EndUpdate();
        }
    }

    private TreeNode? BuildDirectoryNode(string dir, string filter)
    {
        var node = new TreeNode(Path.GetFileName(dir))
        {
            Tag = new NodeInfo(dir, true),
            ImageKey = "folder",
            SelectedImageKey = "folder"
        };

        bool hasMatch = false;

        foreach (var sub in Directory.GetDirectories(dir).OrderBy(p => p))
        {
            var child = BuildDirectoryNode(sub, filter);
            if (child != null) { node.Nodes.Add(child); hasMatch = true; }
        }
        foreach (var file in Directory.GetFiles(dir, "*" + WikiStore.PageExtension).OrderBy(p => p))
        {
            var fileNode = BuildFileNode(file, filter);
            if (fileNode != null) { node.Nodes.Add(fileNode); hasMatch = true; }
        }

        bool nameMatches = filter.Length > 0 &&
            Path.GetFileName(dir).Contains(filter, StringComparison.OrdinalIgnoreCase);

        return (filter.Length == 0 || hasMatch || nameMatches) ? node : null;
    }

    private TreeNode? BuildFileNode(string file, string filter)
    {
        var title = Path.GetFileNameWithoutExtension(file);
        if (filter.Length > 0 && !title.Contains(filter, StringComparison.OrdinalIgnoreCase))
            return null;

        return new TreeNode(title)
        {
            Tag = new NodeInfo(file, false),
            ImageKey = "page",
            SelectedImageKey = "page"
        };
    }

    private NodeInfo? Selected => _tree.SelectedNode?.Tag as NodeInfo;

    /// <summary>Zielordner für neue Einträge, abhängig von der Auswahl.</summary>
    private string TargetDirectory()
    {
        var sel = Selected;
        if (sel == null) return _store.RootDirectory;
        return sel.IsDirectory ? sel.Path : (Path.GetDirectoryName(sel.Path) ?? _store.RootDirectory);
    }

    private void Tree_AfterSelect(object? sender, TreeViewEventArgs e)
    {
        if (e.Node?.Tag is not NodeInfo info || info.IsDirectory)
            return;

        OpenPage(info.Path);
    }

    // ----------------------------------------------------------------- Seiten

    private void OpenPage(string filePath)
    {
        SaveCurrent(); // Aktuelle Seite zuerst sichern.

        _loadingPage = true;
        try
        {
            _currentFile = filePath;
            _editor.Text = _store.ReadPage(filePath);
            _isDirty = false;
            if (_previewMode) RefreshPreview();
            UpdateTitle();
            SetStatus("Geöffnet: " + filePath);
        }
        catch (Exception ex)
        {
            SetStatus("Fehler beim Öffnen: " + ex.Message);
        }
        finally
        {
            _loadingPage = false;
        }
    }

    private void Editor_TextChanged(object? sender, EventArgs e)
    {
        if (_loadingPage) return;
        _isDirty = true;
        UpdateTitle();
    }

    private void SaveCurrent(bool showStatus = false)
    {
        if (_currentFile == null || !_isDirty)
        {
            if (showStatus) SetStatus("Nichts zu speichern.");
            return;
        }

        try
        {
            _store.WritePage(_currentFile, _editor.Text);
            _isDirty = false;
            UpdateTitle();
            if (showStatus) SetStatus("Gespeichert: " + _currentFile);
        }
        catch (Exception ex)
        {
            MessageBox.Show("Speichern fehlgeschlagen:\n" + ex.Message, "Fehler",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void UpdateTitle()
    {
        var name = _currentFile != null ? Path.GetFileNameWithoutExtension(_currentFile) : "Keine Seite";
        Text = $"Personal Wiki — {name}{(_isDirty ? " *" : "")}";
    }

    // ----------------------------------------------------------------- Aktionen

    private void NewCategory()
    {
        var name = Dialogs.Prompt("Neue Kategorie", "Name der Kategorie:", "Neue Kategorie");
        if (name == null) return;

        try
        {
            var path = _store.CreateCategory(TargetDirectory(), name);
            ReloadTree(_search.Text.Trim());
            SelectByPath(path);
            SetStatus("Kategorie erstellt: " + path);
        }
        catch (Exception ex)
        {
            MessageBox.Show("Konnte Kategorie nicht erstellen:\n" + ex.Message, "Fehler",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void NewPage()
    {
        var title = Dialogs.Prompt("Neue Seite", "Titel der Seite:", "Neue Seite");
        if (title == null) return;

        try
        {
            var path = _store.CreatePage(TargetDirectory(), title);
            ReloadTree(_search.Text.Trim());
            SelectByPath(path);
            OpenPage(path);
        }
        catch (Exception ex)
        {
            MessageBox.Show("Konnte Seite nicht erstellen:\n" + ex.Message, "Fehler",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void ImportFiles()
    {
        using var dlg = new OpenFileDialog
        {
            Title = "Dateien ins Wiki importieren",
            Multiselect = true,
            Filter = "Text-/Markdown-Dateien (*.md;*.txt)|*.md;*.txt|Alle Dateien (*.*)|*.*"
        };

        if (dlg.ShowDialog(this) != DialogResult.OK) return;

        var target = TargetDirectory();
        int count = 0;
        string? last = null;
        try
        {
            foreach (var file in dlg.FileNames)
            {
                last = _store.ImportFile(file, target);
                count++;
            }
            ReloadTree(_search.Text.Trim());
            if (last != null) { SelectByPath(last); OpenPage(last); }
            SetStatus($"{count} Datei(en) importiert nach {target}");
        }
        catch (Exception ex)
        {
            MessageBox.Show("Import fehlgeschlagen:\n" + ex.Message, "Fehler",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void RenameSelected()
    {
        var sel = Selected;
        if (sel == null) { SetStatus("Bitte zuerst einen Eintrag auswählen."); return; }

        var currentName = sel.IsDirectory
            ? Path.GetFileName(sel.Path)
            : Path.GetFileNameWithoutExtension(sel.Path);

        var newName = Dialogs.Prompt("Umbenennen", "Neuer Name:", currentName);
        if (newName == null) return;

        try
        {
            // Falls die offene Seite umbenannt wird, vorher sichern.
            if (!sel.IsDirectory && string.Equals(sel.Path, _currentFile, StringComparison.OrdinalIgnoreCase))
                SaveCurrent();

            var newPath = _store.Rename(sel.Path, newName, sel.IsDirectory);

            if (!sel.IsDirectory && string.Equals(sel.Path, _currentFile, StringComparison.OrdinalIgnoreCase))
                _currentFile = newPath;

            ReloadTree(_search.Text.Trim());
            SelectByPath(newPath);
            SetStatus("Umbenannt in: " + newPath);
        }
        catch (Exception ex)
        {
            MessageBox.Show("Umbenennen fehlgeschlagen:\n" + ex.Message, "Fehler",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void DeleteSelected()
    {
        var sel = Selected;
        if (sel == null) { SetStatus("Bitte zuerst einen Eintrag auswählen."); return; }

        var what = sel.IsDirectory ? "die Kategorie samt Inhalt" : "die Seite";
        var name = sel.IsDirectory ? Path.GetFileName(sel.Path) : Path.GetFileNameWithoutExtension(sel.Path);

        var result = MessageBox.Show(
            $"Soll {what} \"{name}\" wirklich gelöscht werden?",
            "Löschen bestätigen", MessageBoxButtons.YesNo, MessageBoxIcon.Warning);

        if (result != DialogResult.Yes) return;

        try
        {
            if (!sel.IsDirectory && string.Equals(sel.Path, _currentFile, StringComparison.OrdinalIgnoreCase))
            {
                _currentFile = null;
                _isDirty = false;
                _loadingPage = true;
                _editor.Clear();
                _loadingPage = false;
                UpdateTitle();
            }

            _store.Delete(sel.Path, sel.IsDirectory);
            ReloadTree(_search.Text.Trim());
            SetStatus("Gelöscht: " + sel.Path);
        }
        catch (Exception ex)
        {
            MessageBox.Show("Löschen fehlgeschlagen:\n" + ex.Message, "Fehler",
                MessageBoxButtons.OK, MessageBoxIcon.Error);
        }
    }

    private void TogglePreview()
    {
        _previewMode = _previewButton.Checked;
        if (_previewMode)
        {
            RefreshPreview();
            _preview.Visible = true;
            _editor.Visible = false;
        }
        else
        {
            _preview.Visible = false;
            _editor.Visible = true;
        }
    }

    private void RefreshPreview()
    {
        _preview.DocumentText = MarkdownRenderer.ToHtml(_editor.Text);
    }

    private void ChangeDataFolder()
    {
        using var dlg = new FolderBrowserDialog
        {
            Description = "Ordner wählen, in dem alle Wiki-Dateien gespeichert werden",
            SelectedPath = _store.RootDirectory,
            UseDescriptionForTitle = true
        };

        if (dlg.ShowDialog(this) != DialogResult.OK) return;

        SaveCurrent();
        AppConfig.Save(dlg.SelectedPath);
        _store = new WikiStore(dlg.SelectedPath);
        _currentFile = null;
        _loadingPage = true;
        _editor.Clear();
        _loadingPage = false;
        UpdateTitle();
        _search.Clear();
        ReloadTree();
        SetStatus("Datenordner: " + _store.RootDirectory);
    }

    private void SelectByPath(string path)
    {
        var node = FindNode(_tree.Nodes, path);
        if (node != null)
        {
            _tree.SelectedNode = node;
            node.EnsureVisible();
        }
    }

    private static TreeNode? FindNode(TreeNodeCollection nodes, string path)
    {
        foreach (TreeNode node in nodes)
        {
            if (node.Tag is NodeInfo info &&
                string.Equals(info.Path, path, StringComparison.OrdinalIgnoreCase))
                return node;

            var found = FindNode(node.Nodes, path);
            if (found != null) return found;
        }
        return null;
    }

    private void MainForm_KeyDown(object? sender, KeyEventArgs e)
    {
        if (e.Control && e.KeyCode == Keys.S)
        {
            SaveCurrent(showStatus: true);
            e.Handled = true;
            e.SuppressKeyPress = true;
        }
    }
}
