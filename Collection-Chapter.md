## 常见集合篇

<img src="http://s5cc1wj96.hd-bkt.clouddn.com/202312151112690.png" alt="image-20231215111211552" style="zoom: 33%;" />

#### List集合

###### ArrayList

底层实现就是数组

其数组的初始化如果不给容量参数，那么就会初始化为0，在我们第一次添加数据的时候才会变成10

其次，在往后的添加数据过程中，只要添加后的容量没有超出底层数组的容量，就会直接添加

否则，就会先将底层数组的数据拷贝到一个长度为1.5倍的数组里，在添加（不是一味的扩容1.5倍，扩容后检测是否超出最大限制）

> 由于是直接拷贝长度，因此扩容后的新数组实际上可能存在脏数据，所以我们取值用的是get方法，他会根据size判断你取值是否越界，避免脏数据



当执行`Arrays.toList`的时候，返回的是一个内部类，不是util中的ArrayList，而且其底层的数组是引用，二者**共用同一地址**

> 无法add操作，底层用了final定义

当执行ArrayList中的toArray的时候，是开辟新的空间，把数据拷贝进去，二者**地址不同**

###### LinkedList

底层是一个双向链表

###### 二者区别

* 底层数据结构不同：ArrayList是一个动态数组，LinkedList是一个双向链表
* 操作数据效率不同
* 内存占用不同：ArrayList使用数组，连续存储，节省内存；LinkedList用的链表，额外存储了prev和next指针
* 二者都不是线程安全的



#### HashMap集合

###### 实现原理

底层使用的是哈希表的结构，发生冲突时候会使用拉链法（后面追加链表）

但是不同的是这里不是简单的链表，当链表的长度达到8以上且数组的长度大于64的时候，会将其转化为红黑树的结构

这样即使在最坏的情况下，查找效率也是$O(log{n})$

> jdk1.8之前用的是链表的结构，之后才引入了红黑树

###### put操作

* 查看当前hashmap有没有被初始化，如果没有就执行扩容
* 根据计算出来的hash值和挡墙容量按位与，得到对应的数组地址
* 如果对应位置为空，直接赋值，不为空则：
  * 查看当前key和数组的key是否一样，一样则为更新操作，直接覆盖
  * 不一样再向其中插入节点，其中如果是红黑树则走红黑树插入的逻辑，是链表直接放到链表尾部，但是链表插入完要看看长度是否超过8，超过的话要转成红黑树结构
  * 其次，插入遍历链表的过程中，发现key一样的直接覆盖
* 上述逻辑执行完，相当于插入了一条数据，都会查看当前元素的数量是否超过数组数量$\times 0.75$，超过则需要扩容

###### 扩容操作

* 先检查有无初始化，没有初始化则初始化为16，直接结束
* 否则，将数组容量$\times 2$，然后遍历原数组的每个元素，如果该元素的next为空，则计算新的hash值插入数组，否则：
  * 是链表，需要对每个元素重新hash再逐个插入
  * 是红黑树，执行红黑树插入

###### 为什么数组长度是2的n次幂

1. 在计算数组位置的时候，可以使用$(capacity-1)\&hash$，而不是模运算，减少开销
2. 在扩容的时候，计算重新计算hash值不是真的重新计算，而是$oldCapacity\&hash$，如果为0则一样，如果为1说明hash的新一位和原来的不一样，则新位置改为：原位置+oldCapacity