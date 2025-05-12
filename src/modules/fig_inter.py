




def fig_inter(py_code, fname, g='globals()'):
    print("正在调用fig_inter工具运行Python代码...")
    import matplotlib
    import os
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    from IPython.display import display, Image

    # 切换为无交互式后端
    current_backend = matplotlib.get_backend()
    matplotlib.use('Agg')

    # 用于执行代码的本地变量
    local_vars = {"plt": plt, "pd": pd, "sns": sns}

    # 相对路径保存目录
    pics_dir = 'pics'
    if not os.path.exists(pics_dir):
        os.makedirs(pics_dir)

    try:
        # 执行用户代码
        exec(py_code, g, local_vars)
        g.update(local_vars)

        # 获取图像对象
        fig = local_vars.get(fname, None)
        if fig:
            rel_path = os.path.join(pics_dir, f"{fname}.png")
            fig.savefig(rel_path, bbox_inches='tight')
            display(Image(filename=rel_path))
            print("代码已顺利执行，正在进行结果梳理...")
            return f"✅ 图片已保存，相对路径: {rel_path}"
        else:
            return "⚠️ 代码执行成功，但未找到图像对象，请确保有 `fig = ...`。"
    except Exception as e:
        return f"❌ 执行失败：{e}"
    finally:
        # 恢复原有绘图后端
        matplotlib.use(current_backend)


fig_inter_tool = {
    "type": "function",
    "function": {
        "name": "fig_inter",
        "description": (
            "当用户需要使用 Python 进行可视化绘图任务时，请调用该函数。"
            "该函数会执行用户提供的 Python 绘图代码，并自动将生成的图像对象保存为图片文件并展示。\n\n"
            "调用该函数时，请传入以下参数：\n\n"
            "1. `py_code`: 一个字符串形式的 Python 绘图代码，**必须是完整、可独立运行的脚本**，"
            "代码必须创建并返回一个命名为 `fname` 的 matplotlib 图像对象；\n"
            "2. `fname`: 图像对象的变量名（字符串形式），例如 'fig'；\n"
            "3. `g`: 全局变量环境，默认保持为 'globals()' 即可。\n\n"
            "📌 请确保绘图代码满足以下要求：\n"
            "- 包含所有必要的 import（如 `import matplotlib.pyplot as plt`, `import seaborn as sns` 等）；\n"
            "- 必须包含数据定义（如 `df = pd.DataFrame(...)`），不要依赖外部变量；\n"
            "- 推荐使用 `fig, ax = plt.subplots()` 显式创建图像；\n"
            "- 使用 `ax` 对象进行绘图操作（例如：`sns.lineplot(..., ax=ax)`）；\n"
            "- 最后明确将图像对象保存为 `fname` 变量（如 `fig = plt.gcf()`）。\n\n"
            "📌 不需要自己保存图像，不需要自己展示图像，函数会自动保存并展示。\n\n"
            "✅ 合规示例代码：\n"
            "```python\n"
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n"
            "import pandas as pd\n\n"
            "df = pd.DataFrame({'x': [1, 2, 3], 'y': [4, 5, 6]})\n"
            "fig, ax = plt.subplots()\n"
            "sns.lineplot(data=df, x='x', y='y', ax=ax)\n"
            "ax.set_title('Line Plot')\n"
            "fig = plt.gcf()  # 一定要赋值给 fname 指定的变量名\n"
            "```"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "py_code": {
                    "type": "string",
                    "description": (
                        "需要执行的 Python 绘图代码（字符串形式）。"
                        "代码必须创建一个 matplotlib 图像对象，并赋值为 `fname` 所指定的变量名。"
                    )
                },
                "fname": {
                    "type": "string",
                    "description": "图像对象的变量名（例如 'fig'），代码中必须使用这个变量名保存绘图对象。"
                },
                "g": {
                    "type": "string",
                    "description": "运行环境变量，默认保持为 'globals()' 即可。",
                    "default": "globals()"
                }
            },
            "required": ["py_code", "fname"]
        }
    }
}