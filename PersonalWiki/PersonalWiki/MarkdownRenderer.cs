using System.Text;
using System.Text.RegularExpressions;

namespace PersonalWiki;

/// <summary>
/// Minimaler Markdown-zu-HTML-Konverter für die Vorschau.
/// Bewusst klein gehalten und ohne externe Bibliotheken – unterstützt die
/// gängigsten Elemente: Überschriften, Listen, Code, Fett/Kursiv, Links,
/// Zitate und Trennlinien.
/// </summary>
public static class MarkdownRenderer
{
    public static string ToHtml(string markdown)
    {
        markdown ??= string.Empty;
        var body = new StringBuilder();
        var lines = markdown.Replace("\r\n", "\n").Replace("\r", "\n").Split('\n');

        bool inUl = false, inOl = false, inCode = false, inQuote = false;

        foreach (var rawLine in lines)
        {
            var line = rawLine;
            var trimmed = line.TrimStart();

            // Code-Block-Begrenzung ```
            if (trimmed.StartsWith("```"))
            {
                if (inCode)
                {
                    body.Append("</code></pre>\n");
                    inCode = false;
                }
                else
                {
                    CloseBlocks(body, ref inUl, ref inOl, ref inQuote);
                    body.Append("<pre><code>");
                    inCode = true;
                }
                continue;
            }

            if (inCode)
            {
                body.Append(Escape(line)).Append('\n');
                continue;
            }

            // Leerzeile beendet offene Blöcke
            if (string.IsNullOrWhiteSpace(line))
            {
                CloseBlocks(body, ref inUl, ref inOl, ref inQuote);
                continue;
            }

            // Trennlinie
            if (trimmed is "---" or "***" or "___")
            {
                CloseBlocks(body, ref inUl, ref inOl, ref inQuote);
                body.Append("<hr/>\n");
                continue;
            }

            // Überschriften (# bis ######)
            var heading = Regex.Match(trimmed, @"^(#{1,6})\s+(.*)$");
            if (heading.Success)
            {
                CloseBlocks(body, ref inUl, ref inOl, ref inQuote);
                int level = heading.Groups[1].Value.Length;
                body.Append($"<h{level}>{Inline(heading.Groups[2].Value)}</h{level}>\n");
                continue;
            }

            // Zitat
            if (trimmed.StartsWith("> "))
            {
                if (!inQuote) { CloseLists(body, ref inUl, ref inOl); body.Append("<blockquote>\n"); inQuote = true; }
                body.Append(Inline(trimmed.Substring(2))).Append("<br/>\n");
                continue;
            }

            // Ungeordnete Liste
            if (trimmed.StartsWith("- ") || trimmed.StartsWith("* "))
            {
                if (inOl) { body.Append("</ol>\n"); inOl = false; }
                if (inQuote) { body.Append("</blockquote>\n"); inQuote = false; }
                if (!inUl) { body.Append("<ul>\n"); inUl = true; }
                body.Append($"<li>{Inline(trimmed.Substring(2))}</li>\n");
                continue;
            }

            // Geordnete Liste (1. 2. ...)
            var ol = Regex.Match(trimmed, @"^\d+\.\s+(.*)$");
            if (ol.Success)
            {
                if (inUl) { body.Append("</ul>\n"); inUl = false; }
                if (inQuote) { body.Append("</blockquote>\n"); inQuote = false; }
                if (!inOl) { body.Append("<ol>\n"); inOl = true; }
                body.Append($"<li>{Inline(ol.Groups[1].Value)}</li>\n");
                continue;
            }

            // Normaler Absatz
            CloseBlocks(body, ref inUl, ref inOl, ref inQuote);
            body.Append($"<p>{Inline(line)}</p>\n");
        }

        // Am Ende offene Blöcke schließen
        if (inCode) body.Append("</code></pre>\n");
        CloseBlocks(body, ref inUl, ref inOl, ref inQuote);

        return Wrap(body.ToString());
    }

    private static void CloseLists(StringBuilder sb, ref bool inUl, ref bool inOl)
    {
        if (inUl) { sb.Append("</ul>\n"); inUl = false; }
        if (inOl) { sb.Append("</ol>\n"); inOl = false; }
    }

    private static void CloseBlocks(StringBuilder sb, ref bool inUl, ref bool inOl, ref bool inQuote)
    {
        CloseLists(sb, ref inUl, ref inOl);
        if (inQuote) { sb.Append("</blockquote>\n"); inQuote = false; }
    }

    /// <summary>Wandelt Inline-Formatierung um (nach HTML-Escaping).</summary>
    private static string Inline(string text)
    {
        text = Escape(text);

        // Inline-Code `...`
        text = Regex.Replace(text, "`([^`]+)`", "<code>$1</code>");
        // Fett **...**
        text = Regex.Replace(text, @"\*\*([^*]+)\*\*", "<strong>$1</strong>");
        // Kursiv *...*
        text = Regex.Replace(text, @"\*([^*]+)\*", "<em>$1</em>");
        // Links [Text](URL)
        text = Regex.Replace(text, @"\[([^\]]+)\]\(([^)]+)\)", "<a href=\"$2\">$1</a>");

        return text;
    }

    private static string Escape(string text) => text
        .Replace("&", "&amp;")
        .Replace("<", "&lt;")
        .Replace(">", "&gt;");

    /// <summary>Bettet den Inhalt in ein schlichtes HTML-Dokument mit Stil ein.</summary>
    private static string Wrap(string innerHtml) =>
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\"/>" +
        "<meta http-equiv=\"X-UA-Compatible\" content=\"IE=edge\"/>" +
        "<style>" +
        "body{font-family:Segoe UI,Arial,sans-serif;font-size:15px;color:#1f1f1f;line-height:1.55;margin:16px;}" +
        "h1,h2,h3,h4{color:#1a3c5e;margin-top:1em;}" +
        "h1{border-bottom:2px solid #e0e0e0;padding-bottom:4px;}" +
        "code{background:#f2f2f2;padding:1px 4px;border-radius:3px;font-family:Consolas,monospace;}" +
        "pre{background:#f6f8fa;padding:10px;border-radius:5px;overflow:auto;}" +
        "pre code{background:none;padding:0;}" +
        "blockquote{border-left:4px solid #c8c8c8;margin:0;padding:4px 12px;color:#555;background:#fafafa;}" +
        "a{color:#1a6fc4;}hr{border:none;border-top:1px solid #ddd;margin:16px 0;}" +
        "</style></head><body>" + innerHtml + "</body></html>";
}
