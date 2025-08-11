## Mendix Python Extension - Beginner's Guide

### What does this tool do?

Welcome to the Mendix Python Extension!

In simple terms, this tool acts as a magical bridge, connecting Mendix Studio Pro with the powerful Python programming language. It allows you to automate repetitive tasks within Mendix using simple Python scripts, such as batch creating pages or modifying data models, thereby saving you significant time and boosting your productivity.

### Prerequisites

Before you begin the installation, please ensure you have the following two items ready on your computer:

1.  **Mendix Studio Pro**: You must have Mendix's development tool installed.
2.  **Python Environment**: Your computer needs to have Python installed.
    - **Version Requirement**: Please install **Python version 3.11 or later**.
    - **How to Install Python**:
      - Visit the official Python website: [https://www.python.org/downloads/](https://www.python.org/downloads/)
      - Download the recommended latest version installer.
      - During installation, **make sure to check the "Add Python to PATH"** option, as shown in the image below, and then click "Install Now" to complete the installation using default settings. This is crucial!

### Installation Steps

Please follow these three steps strictly and one by one.

#### Step 1: Install the Marketplace Plugin in Mendix

We need to download a core plugin from the official Mendix Marketplace.

1.  Open your Mendix Studio Pro.
2.  Locate and click the icon resembling a "shopping cart" in the top right corner to access the App Store / Marketplace.
3.  In the search bar, type `extension mcp server` and press Enter.
4.  Find the plugin named **"extension mcp server"** in the search results, click "Download," and add it to your project.

#### Step 2: Install Python Dependency Packages

This step involves installing the core library for our tool into your Python environment.

1.  Open your computer's "Command Prompt" tool.

    - **Method**: Click the "Start" menu in the bottom left corner of your computer, type `cmd`, and then select "Command Prompt" or "Command Prompt" to open it.

2.  In the black window that appears, copy and paste the following command, then press Enter:

    ```bash
    pip install pymx
    ```

3.  Wait for it to download and install automatically. When you see a message like `Successfully installed pymx...`, it means this step is successful!

### How to Use

After installation, we need to launch Mendix Studio Pro in a special way to activate the extension functionality.

#### Step 1: Create a Dedicated Launch Shortcut

To make future use convenient, let's create a dedicated shortcut.

1.  Locate the installation directory of your Mendix Studio Pro. It's typically found in a path like `C:\Program Files\Mendix\Version Number\modeler\`.
2.  Find the `studiopro.exe` file, right-click on it, and select "**Create shortcut**."
3.  You will see a new icon named "studiopro.exe - Shortcut." Drag it to your desktop.
4.  Right-click on this new shortcut on your desktop and select "**Properties**."
5.  In the window that pops up, find the "**Target**" field. Its content will look something like this:
    `"C:\Program Files\Mendix\10.24.2.75382\modeler\studiopro.exe"`
6.  Now, we need to modify it. At the **end** of the existing content, first **add a space**, and then paste the following text:
    `--enable-extension-development`
    After modification, it should look like this:
    `"C:\Program Files\Mendix\10.24.2.75382\modeler\studiopro.exe" --enable-extension-development`
7.  Click "OK" to save.

You now have a "Developer Mode" launcher!

#### Step 2: Launch and Use

1.  Double-click the desktop shortcut you just created to launch Mendix Studio Pro.
2.  Open your Mendix project using this method (e.g., `D:\Mendix\MyApp\App.mpr`).
3.  Once the project is opened, the Python extension service will automatically start in the background.
4.  In Mendix Studio Pro, click on the top menu bar: `Extensions` -> `StudioProMCP` -> `Start` to launch the MCP service.
5.  Using `claude code` as an example, run the command `claude mcp add --transport http studio_pro http://127.0.0.1:8680/mcp` to configure its usage. VS Code has a similar configuration method.
6.  **How to perform specific actions?**
    - Since specific operations involve writing Python scripts, the best way to learn is by watching our video tutorials. The tutorials will guide you step-by-step on how to write scripts to interact with Mendix.
    - **We highly recommend watching the following video tutorials to get started:**
      - **Bilibili Tutorial**: [https://www.bilibili.com/video/BV1GNtJzfE3W](https://www.bilibili.com/video/BV1GNtJzfE3W)
      - **YouTube Tutorial**: [https://www.youtube.com/watch?v=JHl0or4aRYU](https://www.youtube.com/watch?v=JHl0or4aRYU)

### What to Do If You Encounter Problems

If you run into any issues during installation or usage, don't worry. You can easily find log files and seek assistance.

1.  **Find the Log File**:

    - In Mendix Studio Pro, click `Help` -> `Open Log File Directory` in the top menu bar.
    - This will open a folder. Look for the file named `log.txt` inside it.

2.  **Seek Help**:
    - Open the `log.txt` file and copy all its content.
    - Scan the QR code below to join our WeChat discussion group.
    - Describe the problem you are encountering in the group and paste the log content you just copied. Developers will help you diagnose and solve the issue.

![Scan to join the discussion](wechat.jpg)
