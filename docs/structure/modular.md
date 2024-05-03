# 模块化

虽然在之前的系统设计上，我们称系统中的每一个功能组件都是一个模块，
但实际上在具体的代码实现，每个模块的内部实现不同，导致其具体实现上有一定的差异，
使得我们需要为每个类都涉及一套代码实现，并且还需要手动地加载和连接各个模块。

因此，为了简化这部分的代码开发工作量，让系统本身自动化地完成模块加载和连接，
我们提出了模块化的思想。

> 注意：本系统在代码实现层面不再刻意区分 `interface` 和 `module`，
> 而是在具体的功能性质上有所差异。
> 比如 `interface` 主要负责对外交互，`module` 主要负责内部实现。

## 1. 概念

<!-- 这里模块化思想其实与 Linux 系统中的文件系统如出一辙，
在 Linux 系统中，所有的硬件设备、文件内容和文件夹都属于文件，
共用一套统一的 IO 控制接口。 -->

<!-- 在我们这套系统中也是如此，任何一个具体模块都继承与一个统一的模块接口，
它们共用一套统一的启动、运行和管理接口。
此外，模块之间也能互相嵌套（不允许发生循环依赖），父模块会自动加载子模块。 -->

在本系统中，我们使用 `BasicModule` 来统一所有的模块，
每个具体的模块都拥有其对应的实现。
此后，我们通过 `ModuleManager` 保存每个模块与其基本信息，并进行统一管理。

本系统的生命周期包含两个主要阶段，分别是**加载阶段**和**运行阶段**。
前者主要是在系统初始阶段对模块进行加载，在运行阶段的时候，也可以对模块进行重新加载。
后者则主要是系统从开始到结束这一段时期。

![img](../img/modular.svg)

## 2. 属性

在本项目中，我们使用 `ModuleInfo` 存储每个模块的内部属性。
这些具体的配置信息都会统一存储在 `modules.json` 中间，
由 `ModuleManager` 统一读取和管理。

### 属性内容

-   `name`: 模块名称
-   `alias`: 模块别名（通常指别名）
-   `kind`: 模块的具体实现类型

    > TODO: 补充可支持的模块类型，以便替换

-   `path`: 模块代码所在路径，以便动态导入
-   `modules`: 模块包含的子模块名称
-   `depth`: 模块的嵌套深度
-   `status`: 模块对应的状态

### 具体实现类型

在本项目中，存在某些模块不会出现多个实现类型，也存在模块没有实现类型，
因此我们提供了两种特定实现类型名称。

-   `basic`: 当模块不存在多种实现类型时，则认为是`basic`
-   `null`: 该模块并未实现，在具体加载时会跳过

## 3. 加载阶段

自动加载子模块是模块化系统中最重要的功能之一，
它省去大部分导入模块，设置配置信息和管理子模块的工作，
只需要通过配置文件和少量的代码就可以拉起整个庞大系统。
加载阶段主要是在 `ModuleManager` 中统一处理，
其具体的步骤如下所示。

1. 从配置文件中加载模块基本信息
2. 验证模块之间的依赖关系是否合理
3. 动态加载模块

### a. 加载模块信息

配置文件的具体信息如下，
该配置文件没有使用嵌套的方式存储依赖关系，
仍是使用扁平的方式存储，
在该种配置方式下，就需要通过后期通过程序在再进行解析。

```json
{
    "name": {
        "alias": "alias", // 别名
        "path": "a.b.c", // 路径: 相对src目录, 格式为 a.b.c, 默认为空路径
        "default": "defaultKind", // 默认加载类型: 默认为 basic, 表示只有1个技术实现，
        "modules": ["a", "b"] // 子模块列表:
    }
}
```

### b. 验证模块依赖

在本项目中，模块之间的依赖关系是树状的，
也就是不允许出现环，且每个模块只能被一个父模块所依赖，
因此验证阶段首先会验证依赖的模块是否存在，
然后再通过 BFS 算法验证是否出现循环依赖和交叉依赖。

> TODO: 交叉验证仍未实现

除此之外，在本阶段还能计算出每个子模块的嵌套深度。

### c. 动态加载子模块

动态导入解决如何导入模块的问题，
导入模块所使用的是以下 3 个参数。

-   `path`: 模块所在代码路径
-   `name`: 模块的名字
-   `kind`: 模块的实现类型

最终的引用路径为`path.name.kind`，
当 kind 为 basic 时，将没有`kind`这层路径，
为`null`时，不会加载子模块。
对于具体的对象名称，则是格式为`KindName`的方式进行命名。

## 4. 运行阶段

1. **启动子模块**: 逐一启动运行加载好的模块
2. **加载配置信息**: 从配置文件中重新读取配置文件
3. **模块自检**: 通过调用自定义的检测逻辑，保证模块时可运行的
4. **运行中**: 模块持续在可运行中
5. **等待线程停止**(可选):等待所有线程运行完毕，以优雅停机
6. **停止子模块**: 逐一停止已经运行的模块

当模块运行失败时，需要通过停止操作将所有子模块关闭停止。

### a. 钩子函数

每个模块而言可能存在一些自定义的加载逻辑，
在本系统中我们通过钩子函数进行实现。
通过重写钩子函数，自定义的加载逻辑就可以在对应的启动的生命周期中运行。
目前提供的钩子函数如下。

-   运行子模块前
-   运行当前模块前
-   运行当前模块后

> 注意：运行成功前后这两个钩子函数，主要针对 `is_running` 这个状态变量改变前后。
> 因为 `is_running` 可能会影响一些持久运行的线程，这个在后面的内容会介绍。

### b. 多线程

某些模块在启动之后，需要持续的运行处理，
因此需要使用多线程的技术。
本系统为了对多线程的创建和回收进行统一的管理，
因此封装了 `make_thread` 用于创建和运行线程。
该函数创建的线程对象会存储在模块内部，
开发者需要自行选择合适的钩子函数作为时机，创建和运行线程。

在线程内部，通常使用死循环的方式进行循环操作，以保证可持续运行。
但是在实际实现上，最好通过一些标志位来停止这个死循环操作，
以进行优化的停止。目前是推荐 `is_running` 状态类控制。

> 注意：未来可能会通过其他的标志状态来控制这个线程的运行情况。