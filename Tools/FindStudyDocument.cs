using System;
using System.IO;
using System.Runtime.InteropServices;
using System.Runtime.InteropServices.ComTypes;
using System.Threading;
using Microsoft.Build.Framework;
using Microsoft.Build.Utilities;

public sealed class FindStudyDocument : Task
{
    [DllImport("ole32.dll")]
    private static extern int GetRunningObjectTable(int reserved, out IRunningObjectTable table);

    [DllImport("ole32.dll")]
    private static extern int CreateBindCtx(int reserved, out IBindCtx context);

    [Required]
    public string SolutionFile { get; set; }

    [Output]
    public string SourceFile { get; set; }

    public override bool Execute()
    {
        // The build may run in a different process from the IDE. Match the full
        // solution path so an unrelated Visual Studio window cannot select a file.
        for (int attempt = 0; attempt < 10; attempt++)
        {
            bool busy = false;
            try
            {
                SourceFile = FindActiveDocument(ref busy);
                if (!string.IsNullOrEmpty(SourceFile))
                    return true;
            }
            catch (Exception error)
            {
                Log.LogError(error.Message);
                return false;
            }
            if (!busy) break;
            Thread.Sleep(150);
        }
        Log.LogError("Could not read the active document. Open a saved problem .cpp in the editor and press F5 again.");
        return false;
    }

    private string FindActiveDocument(ref bool busy)
    {
        IRunningObjectTable table;
        IBindCtx context;
        Marshal.ThrowExceptionForHR(GetRunningObjectTable(0, out table));
        Marshal.ThrowExceptionForHR(CreateBindCtx(0, out context));
        IEnumMoniker entries;
        table.EnumRunning(out entries);
        var entry = new IMoniker[1];
        try
        {
            while (entries.Next(1, entry, IntPtr.Zero) == 0)
            {
                try
                {
                    string name;
                    entry[0].GetDisplayName(context, null, out name);
                    if (!name.StartsWith("!VisualStudio.DTE.", StringComparison.OrdinalIgnoreCase))
                        continue;
                    object instance;
                    table.GetObject(entry[0], out instance);
                    dynamic ide = instance;
                    if (string.Equals((string)ide.Solution.FullName, Path.GetFullPath(SolutionFile),
                                      StringComparison.OrdinalIgnoreCase))
                    {
                        dynamic document = ide.ActiveDocument;
                        return document == null ? null : (string)document.FullName;
                    }
                }
                catch (COMException error)
                {
                    // Other instances may be closing, elevated, or temporarily busy.
                    busy |= error.HResult == unchecked((int)0x80010001) ||
                            error.HResult == unchecked((int)0x8001010A);
                }
                catch (UnauthorizedAccessException) { }
                finally { Marshal.ReleaseComObject(entry[0]); }
            }
        }
        finally
        {
            Marshal.ReleaseComObject(entries);
            Marshal.ReleaseComObject(context);
            Marshal.ReleaseComObject(table);
        }
        return null;
    }
}
