<#
.SYNOPSIS
    合并多个项目的 src 代码。
    1. 修复了 Write-Host 报错。
    2. 修复了 Markdown 反引号转义报错。
    3. 增加了排除 *.editorConfig.ts 和 *.editorPreview.tsx 的逻辑。
#>

param (
    [Parameter(Mandatory=$true, Position=0, ValueFromRemainingArguments=$true)]
    [string[]]$TargetRoots
)

# ----------------------
# 1. 确定主输出路径
# ----------------------
try {
    $MainRootItem = Get-Item -Path $TargetRoots[0] -ErrorAction Stop
    $MainRootPath = $MainRootItem.FullName
}
catch {
    Write-Error "错误: 无法解析路径 '$($TargetRoots[0])'。"
    exit 1
}

$OutputFile = Join-Path $MainRootPath "kb.md"

# 初始化 kb.md
$ProjectList = $TargetRoots -join ', '
$HeaderInfo = "# 项目源代码合并文档`n`n**生成时间**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n**包含项目**: $ProjectList`n`n---`n"
Set-Content -Path $OutputFile -Value $HeaderInfo -Encoding utf8

# ----------------------
# 2. 循环处理项目
# ----------------------
$TotalFiles = 0

foreach ($rawPath in $TargetRoots) {
    if (-not (Test-Path $rawPath)) { continue }
    
    $RootItem = Get-Item -Path $rawPath
    $RootPath = $RootItem.FullName
    $ProjectName = $RootItem.Name

    Write-Host "正在处理: $ProjectName ..." -ForegroundColor Cyan

    # -------------------------------------------------------------
    # 核心修改点：增加文件名排除逻辑
    # -------------------------------------------------------------
    $files = Get-ChildItem -Path $RootPath -Recurse -File | Where-Object {
        # 1. 必须是 cs 或 tsx
        ($_.Extension -eq ".py" -or $_.Extension -eq ".md") -and
        
        # 2. 排除测试和类型定义目录
        ($_.FullName -notmatch "[\\/]__tests__[\\/]") -and
        ($_.FullName -notmatch "[\\/]typings[\\/]") -and
        
        # 3. 排除特定配置文件 (新增逻辑)
        ($_.Name -notlike "debug*") -and
        ($_.Name -notlike "*.editorPreview.tsx")
    }

    if ($files.Count -eq 0) { continue }

    # 添加项目分割头
    Add-Content -Path $OutputFile -Value "`n# 项目: $ProjectName`n" -Encoding utf8

    # 自动加入脚本同级目录下的 env.spec.md (如果存在)
    $EnvSpecFile = Join-Path $PSScriptRoot "env.spec.md"
    if (Test-Path $EnvSpecFile) {
        $files = @($files) + (Get-Item $EnvSpecFile)
    }
    foreach ($file in $files) {
        $TotalFiles++
        
        # 1. 计算相对路径
        $relativePath = $file.FullName.Substring($RootPath.Length).TrimStart('\', '/').Replace('\', '/')
        
        # 2. 确定语言
        $lang = switch ($file.Extension.ToLower()) {
            ".js"   { "javascript" }
            ".ts"   { "typescript" }
            ".tsx"  { "typescript" }
            ".html" { "html" }
            ".css"  { "css" }
            ".java" { "java" }
            ".cs"   { "csharp" }
            ".py"   { "python" }
            ".md"   { "markdown" }
            ".json" { "json" }
            ".sql"  { "sql" }
            ".sh"   { "bash" }
            default { "" } # 默认不显示语言名，由 Markdown 自动处理
        }

        # 3. 读取内容
        $content = Get-Content -Path $file.FullName -Raw -Encoding utf8

        # 4. 构造 Markdown 块
        # 使用单引号拼接 '```'，彻底解决转义报错问题
        $mdBlock = "`n## [$ProjectName] $relativePath`n`n" + '```' + "$lang`n$content`n" + '```'

        # 5. 写入
        Add-Content -Path $OutputFile -Value $mdBlock -Encoding utf8
    }
}

Write-Host "--------------------------------------------------" -ForegroundColor Green
Write-Host "完成! 已合并 $TotalFiles 个文件。" -ForegroundColor Green
Write-Host "输出文件: $OutputFile" -ForegroundColor Yellow
Write-Host "--------------------------------------------------" -ForegroundColor Green