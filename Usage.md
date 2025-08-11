## Mendix Python 扩展 - 新手入门指南

### 这个工具是做什么的？

欢迎使用 Mendix Python 扩展！

简单来说，这个工具就像一个神奇的桥梁，它连接了 Mendix Studio Pro 和强大的 Python 编程语言。通过它，您可以使用简单的 Python 脚本来自动完成 Mendix 中的重复工作，比如批量创建页面、修改数据模型等，从而大大节省您的时间，提高工作效率。

### 准备工作

在开始安装之前，请确保您的电脑上已经准备好以下两样东西：

1.  **Mendix Studio Pro**：您必须已经安装了 Mendix 的开发工具。
2.  **Python 环境**：您的电脑需要安装 Python。
    - **版本要求**：请安装 **3.11 或更高版本** 的 Python。
    - **如何安装 Python**：
      - 访问 Python 官方网站：[https://www.python.org/downloads/](https://www.python.org/downloads/)
      - 下载推荐的最新版本安装包。
      - 运行时，请**务必勾选 "Add Python to PATH"** 选项，如下图所示，然后点击 "Install Now" 使用默认设置完成安装。这非常重要！

### 安装步骤

请严格按照以下三个步骤操作，一步一步来。

#### 第一步：在 Mendix 中安装市场插件

我们需要从 Mendix 的官方市场（Marketplace）中下载一个核心插件。

1.  打开您的 Mendix Studio Pro。
2.  在右上角找到并点击像“购物车”一样的图标，进入 App Store / Marketplace。
3.  在搜索框中，输入 `extension mcp server` 然后按回车。
4.  在搜索结果中找到名为 **"extension mcp server"** 的插件，点击 "Download" 下载并将其添加到您的项目中。

#### 第二步：安装 Python 依赖包

这一步是为您的 Python 环境安装我们这个工具的核心库。

1.  打开电脑的“命令提示符”工具。

    - **方法**：点击电脑左下角的“开始”菜单，直接输入 `cmd`，然后选择“命令提示符”或 "Command Prompt" 打开。

2.  在弹出的黑色窗口中，复制并粘贴以下命令，然后按回车键：

    ```bash
    pip install pymx
    ```

3.  等待它自动下载和安装。当您看到类似于 `Successfully installed pymx...` 的提示时，就代表这一步成功了！

### 如何使用

安装完成后，我们还需要用一种特殊的方式来启动 Mendix Studio Pro，才能激活这个扩展功能。

#### 第一步：创建专用的启动快捷方式

为了方便以后使用，我们创建一个专用的快捷方式。

1.  找到您 Mendix Studio Pro 的安装位置。通常在 `C:\Program Files\Mendix\版本号\modeler\` 目录下。
2.  找到 `studiopro.exe` 这个文件，在它上面点击鼠标右键，选择 “**创建快捷方式**”。
3.  您会看到一个名为 “studiopro.exe - 快捷方式” 的新图标。把它拖到您的桌面上。
4.  在桌面上的这个新快捷方式上点击鼠标右键，选择 “**属性**”。
5.  在弹出的窗口中，找到 “**目标(T)**” 这一栏。它的内容类似这样：
    `"C:\Program Files\Mendix\10.24.2.75382\modeler\studiopro.exe"`
6.  现在，我们需要修改它。在原有内容的**末尾**，先**加一个空格**，然后粘贴以下文本：
    `--enable-extension-development`
    修改后，它看起来会像这样：
    `"C:\Program Files\Mendix\10.24.2.75382\modeler\studiopro.exe" --enable-extension-development`
7.  点击“确定”保存。

现在，您就有了一个“开发者模式”的启动器了！

#### 第二步：启动并使用

1.  双击我们刚刚创建的那个桌面快捷方式，启动 Mendix Studio Pro。
2.  用这个方式打开您的 Mendix 项目（例如：`D:\Mendix\MyApp\App.mpr`）。
3.  当项目打开后，Python 扩展服务就会自动在后台启动。
4.  在 Mendix Studio Pro 的顶部菜单栏，点击 `Extensions` -> `StudioProMCP` -> `Start`启动 MCP 服务。
5.  以 claude code 为例，运行命令`claude mcp add --transport http studio_pro http://127.0.0.1:8680/mcp`配置使用，vscode 有类似配置方式。
6.  **如何具体操作？**
    - 由于具体的操作涉及到编写 Python 脚本，最好的学习方式是观看我们的视频教程。教程会手把手教您如何写脚本与 Mendix 交互。
    - **强烈推荐观看以下视频教程入门：**
      - **Bilibili 教程**: [https://www.bilibili.com/video/BV1GNtJzfE3W](https://www.bilibili.com/video/BV1GNtJzfE3W)
      - **YouTube 教程**: [https://www.youtube.com/watch?v=JHl0or4aRYU](https://www.youtube.com/watch?v=JHl0or4aRYU)

### 遇到问题怎么办？

如果在安装或使用过程中遇到任何问题，别担心，您可以轻松地找到日志文件，并寻求帮助。

1.  **找到日志文件**：

    - 在 Mendix Studio Pro 的顶部菜单栏，点击 `Help` -> `Open Log File Directory`。
    - 这会打开一个文件夹，在里面找到名为 `log.txt` 的文件。

2.  **寻求帮助**：
    - 打开 `log.txt` 文件，将里面的所有内容复制下来。
    - 扫描下方的二维码，加入我们的微信讨论群。
    - 在群里描述您遇到的问题，并附上您刚刚复制的日志内容，开发者会帮您定位和解决问题。

![扫码参与讨论](wechat.jpg)
