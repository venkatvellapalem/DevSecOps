# PDF exports

`DevSecOps_Secure_Pipeline.pdf` — the deck, for presenting on a machine without
PowerPoint, and for sharing with anyone who will not open a `.pptx`.

The four Word documents are **not** exported here. Word's COM automation is
unreliable on this machine: it answers `ComputeStatistics` without trouble but
hangs indefinitely on `ExportAsFixedFormat`, and left stale `WINWORD` processes
behind on every attempt. Rather than ship a half-working script, export them from
Word directly:

**File → Export → Create PDF/XPS**

To regenerate the deck PDF with PowerPoint COM (this one does work):

```powershell
$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Open("...\DevSecOps_Secure_Pipeline.pptx", $true, $false, $false)
$pres.SaveAs("...\pdf\DevSecOps_Secure_Pipeline.pdf", 32)
$pres.Close(); $pp.Quit()
```
