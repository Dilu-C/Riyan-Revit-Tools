param(
    [string]$PdfPath,
    [string]$PngPath,
    [int]$Width = 2400,
    [int]$PageIndex = 0
)

Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
$asTaskAction = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' } | Select-Object -First 1

[Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime] | Out-Null

$fileOp = [Windows.Storage.StorageFile]::GetFileFromPathAsync($PdfPath)
$fileTask = $asTaskGeneric.MakeGenericMethod([Windows.Storage.StorageFile]).Invoke($null, @($fileOp))
$fileTask.Wait()
$file = $fileTask.Result

$pdfOp = [Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($file)
$pdfTask = $asTaskGeneric.MakeGenericMethod([Windows.Data.Pdf.PdfDocument]).Invoke($null, @($pdfOp))
$pdfTask.Wait()
$pdfDoc = $pdfTask.Result

$idx = [Math]::Max(0, [Math]::Min([int]($pdfDoc.PageCount - 1), $PageIndex))
$page = $pdfDoc.GetPage($idx)

if (Test-Path $PngPath) { Remove-Item $PngPath -Force }
$dir = [System.IO.Path]::GetDirectoryName($PngPath)
$name = [System.IO.Path]::GetFileName($PngPath)

$folderOp = [Windows.Storage.StorageFolder]::GetFolderFromPathAsync($dir)
$folderTask = $asTaskGeneric.MakeGenericMethod([Windows.Storage.StorageFolder]).Invoke($null, @($folderOp))
$folderTask.Wait()
$folder = $folderTask.Result

$createOp = $folder.CreateFileAsync($name, [Windows.Storage.CreationCollisionOption]::ReplaceExisting)
$createTask = $asTaskGeneric.MakeGenericMethod([Windows.Storage.StorageFile]).Invoke($null, @($createOp))
$createTask.Wait()
$outFile = $createTask.Result

$streamOp = $outFile.OpenAsync([Windows.Storage.FileAccessMode]::ReadWrite)
$streamTask = $asTaskGeneric.MakeGenericMethod([Windows.Storage.Streams.IRandomAccessStream]).Invoke($null, @($streamOp))
$streamTask.Wait()
$stream = $streamTask.Result

$renderOptions = New-Object Windows.Data.Pdf.PdfPageRenderOptions
$renderOptions.DestinationWidth = $Width

$renderOp = $page.RenderToStreamAsync($stream, $renderOptions)
$renderTask = $asTaskAction.Invoke($null, @($renderOp))
$renderTask.Wait()
$stream.Dispose()
