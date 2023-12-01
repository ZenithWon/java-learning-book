# Java八股文笔记

### Redis篇

**缓存穿透**

**产生原因**：当查询的数据不存在时，由于缓存中一定没有，那么请求就会直接被转发至数据库，给数据库造成很大的压力

**解决方案**

1. 缓存空数据：查询数据库的结果尽管为空，也可以向缓存中插入一条空数据，不过可以将空数据的ttl时间设置的短一点。
2. 布隆过滤器：在查询redis之前可以先去访问布隆过滤器，如果返回不存在则直接返回，如果返回存在则再执行后面的查询业务。

![image-20231130140657932](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130140657932.png)

> 注：布隆过滤器返回不存在一定不存在，但是返回存在只是代表数据可能存在。

**布隆过滤器（Bloom filter）**

对于给定的key，过滤器会通过$N$个不同的哈希函数计算出$N$个哈希值，然后将bitmap中对应位置的bit置为1

当查询某个key的时候，同样会用这$N$个哈希函数计算哈希值，然后查看这个$N$个bit位，只要有一个不为1则返回false，否则返回true

![image-20231130140813783](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130140813783.png)

**缓存击穿**

**产生原因**：对于某个redis中不存在的key，其缓存重建的时间很长，恰好又有大量并发请求出现，那么就会全部达到数据库造成数据库崩溃

**解决方案**

1.  互斥锁

    所有相同的并发请求会全部争抢同一个锁（一般用分布式锁实现），这样有且仅有一个线程可以争抢到

    争抢到锁的线程会去访问数据库，执行缓存重建的业务

    没有争抢的线程则会被阻塞一段时间，醒来后查询缓存，如果缓存中存在数据则返回，不存在则会继续争抢锁。

    ![image-20231130141650119](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130141650119.png)
2.  逻辑过期

    这里不在给数据设置ttl，而是在数据创建的时候直接放入缓存，但是会添加一个逻辑过期字段。

    当从缓存中查到的数据发现是过期的时候，线程会去获取锁。

    获取锁成功后，会开启一个独立的线程去执行缓存重建业务，并且由这个新的线程释放锁，当前线程则会立即返回过期的旧数据。

    获取锁失败则会直接返回旧数据，而不是阻塞循环等待。

    ![image-20231130142038996](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130142038996.png)

**二者的比较**

互斥锁方案可以保证数据的强一致性，但是由于阻塞循环等待会导致性能较差

逻辑过期方案可以保证数据的高可用性，但是无法保证数据的绝对一致。

> 数据的可用性和一致性是无法同时保障的。

**缓存雪崩**

**产生原因**：当大量的数据同时过期或者redis服务直接宕机，就会导致大量请求到达数据库，造成数据库崩溃

**解决方案**

1. 为防止大量key同时过期，可以在给数据的ttl添加上一个随机值，保证不在同一时刻过期
2. 对于redis服务宕机的情况
   * 设置redis集群：使用哨兵机制、主从模式集群等
   * 使用多级缓存技术：客户端缓存 -> nginx缓存 -> redis缓存 -> 本地缓存(Caffiene、Map) -> 数据库
   * 使用降级限流策略

> 降级限流策略可以作为系统的保底策略，也可以用来解决缓存击穿、穿透问题，比如逻辑过期返回旧数据也可以看作是一种降级策略

**双写一致性**

**读操作**：缓存hit则直接返回，miss则去查询数据库，写入缓存再返回数据。

**写操作**：采用延迟双删策略

![image-20231130143149918](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130143149918.png)

由于不管是先删除缓存再修改数据库，还是先修改数据库在删除缓存都会导致数据的不一致性，因此这里使用双删的策略。

延时的原因是需要等待数据库的主从库同步完，再清理一次缓存中的脏数据。

但是延迟双删仍然无法保证数据的一致性。

**一致性实现**

*   **强一致性**：使用读写锁实现

    当数据库存在写操作时，会设置一把写锁，后面来的请求不管是读数据还是写数据都需要等待当前写进程执行完

    当数据库存在读操作时，会设置一把读锁，后面来的请求如果是读操作则可以共享，如果为写操作则需要等待全部读操作执行完。

    > 读锁是一把共享锁，写锁是一把排他锁
*   **最终一致性**：使用异步通知实现

    修改数据的时候不直接同时操作缓存和数据库，而是操作完数据库后发布一条消息，缓存服务会持续监听该信道的消息，然后更新自己的缓存。

    ![image-20231130144355209](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130144355209.png) ![image-20231130144447471](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130144447471.png)

**数据持久化**

**RDB方式**

RDB会将redis的内存数据全部记录到磁盘上，相当于一个快照，当redis故障需要恢复数据的时候就会读取快照，重新加载数据。

有两种方式：save和bgsave。前者是用redis的主进程，会阻塞所有其他命令；后者是fork一个子进程，在后台执行保存。

**RDB执行原理**

![image-20231130150718867](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130150718867.png)

**AOF方式**

AOF文件会记录redis每个写操作命令，当需要恢复的时候则会执行AOF文件中的每条命令。

为防止记录过多无效写命令，可以使用bgrewriteof命令，执行AOF重写功能，用最少的命令实现相同的效果。

**二者对比**

|        |           RDB          |       AOF      |
| :----: | :--------------------: | :------------: |
|  持久化方式 |       定期对整个内存做快照       |   记录每一条写操作命令   |
|  数据完整性 |      两次备份之间可能会丢失数据     |   取决于配置文件中的策略  |
|  文件大小  |          文件体积小         |   记录命令，文件体积大   |
| 宕机恢复速度 |     快，只是将RDB文件加载到内存    |   慢，需要逐条执行命令   |
| 系统资源占用 |       高，需要耗费大量内存       |   低，仅仅只是记录命令   |
|  使用场景  | 可以容忍数分钟的数据丢失，追求更快的启动速度 | 需要提供较高的数据安全性保障 |

**数据过期策略**

**定义**：数据过期，如何从内存中删除

**惰性删除**：设置过期时间后不去管，需要该key的时候先查看是否过期，如果过期再去删除它。

但是这种方式，会导致过期且从来不会访问的key一直存在于内存中，内存永远无法被释放。

**定期删除**：每隔一段时间，就会对一部分key检查，删除其中过期的key。这里每次检查是部分检查，不是全量检查，只需要保证一个周期可以检查所有就好。

> redis使用这两种策略的结合。不仅会定期删除，而且在查询的时候也会检查。

**数据淘汰策略**

**定义**：当redis内存不够时，如果向redis添加新的key，应该如何删除内存中的数据，从而保证新数据的添加。

**8种策略**

1. noeviction：内存满了不允许写入
2. volatile-ttl：对设置了ttl的key，删除最快要过期的数据
3. allkeys-random：对全体key随机删除
4. volatile-random：对设置了ttl的key，随机删除
5. allkeys-lru：对所有的key，使用LRU算法
6. volatile-lru：对设置里ttl的key，使用LRU算法
7. allkeys-lfu：对所有的key，使用LFU算法
8. volatile-lfu：对设置里ttl的key，使用LFU算法

> LRU算法：最近最少未使用；LFU算法：最少频率使用

**分布式锁**

**SETNX实现**

分布式锁的实现底层原理就是利用setnx命令，如果存在则无法set，这样只会有一个线程成功set获取锁。

但是为了实现获取锁和解锁的原子性，会使用`set key threadId nx ex ttl`命令来获取锁，并使用lua脚本释放锁（包括比对线程ID以及delete操作）。

**Redisson分布式锁**

使用redisson可以实现对锁的自动续期操作，使用看门狗机制，开启一个新的线程watchDog，不断的给锁续期

![image-20231130164235357](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130164235357.png)

redisson还可以设置锁的重试时间，不会获取失败直接返回，也不会循环无线等待

![image-20231130164302414](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130164302414.png)

**Redisson可重入锁**

为了防止线程获取到锁后调用其他函数再次获取同一把锁失败，redisson设计了的锁是一把可重入锁

在执行setnx命令时，不是简单的给key设置一个threadId的value，而是设置一个hash结构。其filed是threadId，value是重入的次数。

* trylock：会查看锁是否存在，不存在直接setnx，存在则会查看threadId，如果一样则将value+1，否则获取锁失败
* unlock：会查看当前value值，如果大于1则执行value-1，否则直接删除key

**分布式锁的主从一致性**

由于redis的主从是读写分离的，如果一个线程刚设置完锁，但是还没来的及同步给从库，master就崩了，那么新的master中是没有这把锁的。

![image-20231130164929225](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130164929225.png)

可以使用redis的红锁实现，即每次创建锁的时候需要在$\frac{n}{2}+1$个节点上创建该锁，否则无法获取这把锁

因此就算有一个节点宕机了，其他的服务器还是有这把锁的，其他线程无法获得

**Redis集群-主从复制**

**定义**：顾名思义，一个master连接若干个slave。并且读写分离，master写，slave读

**全量同步**

slave建立连接后，会发送携带id（初始值为自己的id）和offset（初始值为0）同步请求。master判断是否是第一次同步，即比对id是否一样。

如果不一样说明第一次，则执行**全量同步**，并返回当前自己的id和offset。

然后master会在后台执行bgsave命令，生成完RDB文件后会发送给slave，slave收到后直接覆盖自己的内存加载RDB文件。

但是在bgsave的时候也会有新的写请求，因此master还需要同步维护一个类似AOF的文件，称为repl\_baklog，master会根据上一次的offset发送repl\_baklog文件对应的内容发送给slave，slave收到后更新数据并且更新自己的offset

![image-20231130171940263](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130171940263.png)

**增量同步**

如果slave重启或者数据变化，那么就会执行增量同步。

slave携带id和offset请求同步后，master发现id一致，那么就会执行增量同步。

然后从repl\_baklog中offset以后的数据发送给slave，slave收到后更新数据并且更新自己的offset

![image-20231130172216554](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130172216554.png)

**Redis集群-哨兵模式**

哨兵模式（sentinel）用于实现主从集群的自动故障恢复

**作用**

1. 监控master和slave是否在按照预期正常运作
2. 如果master故障，sentinel会从slave中选取一个作为新的master，即使原本的master恢复，也只能成为新master的slave
3. 通知redis客户端主从发生变化，防止客户端违规的向原本的master写数据（可能成为slave或者还在故障中）

![image-20231130174229378](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130174229378.png)

**服务状态监控工作原理**

基于心跳机制检测，一旦有一个sentinel发现ping不通某个node就会认为该node主观下线。

一旦有超过一定数量（自己配置）的sentinel都认为该node主观下线，则该node客观下线（真的下线）

如果认为客观下线的node是master则会通过以下方式选举新的master：

* 根据设定的优先级选择slave作为master
* 如果优先级一样，选offset最大的slave

**脑裂问题**

由于网络原因，sentinel无法连接到master认为其下线从而选出新的master。但是客户端仍可以与原本的master连接，因此在主从切换的过程中，原本的matser仍然在接收写命令。

但是一旦网络恢复，原本的master会变为slave，他会清空原本写入的数据，和新的master做全量同步，这会导致在主从切换过程中写入的数据发生丢失。

可以通过设置两个参数来解决

* `min-replicas-to-write`：表示最少的从节点个数，如果不满足则不允许执行写操作
* `min-replicas-max-lag`：表示数据复制时的 ACK 消息延迟的最大时间。主库做同步时，如果没有在指定时间返回ACK，则拒绝写入数据。

**Redis集群-分片集群**

在分片集群中，有很多的master，每个master保存一部分数据，这样就可以实现高并发写操作以及海量数据存储问题

每个master还可以有自己的slave实现高并发读操作

各个master之间互相通过心跳机制监控，不需要哨兵机制

**插槽**

为了实现访问任何节点都可以得到同一个数据，redis使用了一种插槽的概念

插槽的总数是16384个，对于请求的key，会根据key做hash然后对16485取模。

redis给每个master都分配了插槽，如果当前访问的节点发现算出来的结果不是自己的槽就会根据值路由到其他redis节点，否则从自己的内存中查出来返回。

![image-20231130175653818](https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231130175653818.png)

**Redis的单线程问题**

### Mysql篇

11111
