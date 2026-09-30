# PDF exports

`DevSecOps_Secure_Pipeline.pdf` — the deck, for presenting on a machine without
PowerPoint, and for sharing with anyone who will not open a `.pptx`.

Export a fresh copy after editing the deck:

```powershell
$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Open("...\DevSecOps_Secure_Pipeline.pptx", $true, $false, $false)
$pres.SaveAs("...\pdf\DevSecOps_Secure_Pipeline.pdf", 32)
$pres.Close(); $pp.Quit()
```

The Word documents are not exported here. Word's COM automation hung repeatedly
on this machine (stale `WINWORD` processes had to be killed twice), so it was
abandoned rather than left half-working. Export them from Word directly:
**File -> Export -> Create PDF/XPS**.
