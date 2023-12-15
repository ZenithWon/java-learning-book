## 微服务篇

#### 微服务组件

###### **Spring Cloud**

注册中心（Eureka）、负载均衡（Ribbon）、远程调用（Feign）、熔断降级（Hystrix）、网关（Gateway）

###### **Spring Cloud Alibaba**

注册中心（Nacos）、负载均衡（Ribbon）、远程调用（Feign）、熔断降级（Sentinel）、网关（Gateway）



#### 注册中心

* 服务注册：服务提供者需要把自己的信息注册到注册中心，由注册中心保存这些信息，比如服务名称、IP、端口等
* 服务发现：当消费者需要远程调用的时候，会请求注册中心获取服务的信息，如果是一个服务集群，那么会通过Ribbon负载均衡算法，选择其中一个实例调用
* 服务监控：注册中心会实时监控服务的健康状态，一旦发现某个实例下线，就会从自己的服务列表中剔除掉，比如通过心跳的机制监控

常用的注册中心有两个，分别是Nacos和Eureka，二者区别在于：

* Nacos的非临时实例，不是由实例自己向nacos发送心跳，而是由nacos会主动向实例发送心跳，但是Eureka没有临时实例这种概念

* 当有服务实例的信息发送变更，nacos会主动向其他服务推送变更信息，但是eureka没有推送的操作



#### 负载均衡

###### **Ribbon流程**

当消费者需要远程调用的时候，会请求注册中心获取服务的信息，如果是一个服务集群，那么会通过Ribbon负载均衡算法，选择其中一个实例调用

###### **负载均衡算法**

* RoundRobinRule：简单轮询算法
* WeightResponseTimeRule：按照权重来选择服务器，响应时间越长权重越小
* RandomRule：随机选
* ZoneAvoidanceRule：使用Zone对服务器分类，优先对同一区域的服务器轮询，都没有才会去其他Zone轮询
* BestAvailableRule：忽略短路的服务器，并选择并发数少的服务器
* RetryRule：先通过轮询访问，如果服务器失效会一直重试
* AvailableFilteringRule：先过滤非健康的，然后再去选择连接数小的服务器

> 前四个比较重要

###### **自定义负载均衡策略**

实现IRule接口，并交给容器管理

或者在配置文件中给每个单独的服务自定义负载均衡策略



#### 服务雪崩

在服务的远程调用中，一旦一个服务不可用，会导致整个调用链都不可用

<img src="http://s5cc1wj96.hd-bkt.clouddn.com/image-20231208165935723.png" alt="image-20231208165935723" style="zoom: 50%;" />

解决方案：使用熔断降级解决，同时使用限流预防

###### 熔断降级

服务降级是一种服务的自我保护方式，确保在服务不可用的时候服务不会崩溃。其实就是服务在不可用的时候，回复一个default response

服务熔断，用于检测服务调用的情况，如果服务降级过于频繁，那么会直接禁止请求该服务直接降级，之后每隔一段时间都会请求一次服务，如果成功就会恢复正常。

> 注意：服务熔断会直接停止访问该服务，其实其他的接口是好的也无法访问，而服务降级仅仅针对于不可用的接口

<img src="http://s5cc1wj96.hd-bkt.clouddn.com/image-20231208172908845.png" alt="image-20231208172908845" style="zoom:50%;" />

这里推荐使用FallbackFactory实现，而不是使用Fallback。因为工厂对象可以获取异常信息，方便分析

```java
//Using fallback factory can catch exception info
@Component
public class UserFeignClientFallbackFactory implements FallbackFactory<UserFeignClient> {
    @Override
    public UserFeignClient create(Throwable throwable) {
        return new UserFeignClient() {
            @Override
            public R getUserById(Long id) {
                User user=new User();
                user.setId(999999L);
                user.setUsername("default user (Fallback)");
                return R.ok(user);
            }
        };
    }
}
```



#### 微服务限流

###### 限流原因

1. 防止并发量过大
2. 防止用户恶意刷接口

###### 限流方式

1. Tomcat限制最大连接数，一般适用于单体项目
2. Nginx，使用漏桶算法
3. Gateway，令牌桶算法
4. 自定义拦截器

###### Nginx漏桶算法

使用一个缓冲区用于接收请求，然后以固定速率发出请求，如果缓冲区满了，就不接受请求。其实就是一个缓冲区队列

###### Gateway令牌桶算法

<img src="http://s5cc1wj96.hd-bkt.clouddn.com/202312121413319.png" alt="image-20231212141255530" style="zoom:50%;" />

和漏桶算法相似，但是一个存储的是请求一个存储的是令牌

网关会以固定的速率生成令牌存放到桶中，桶满了就会停止生成

当请求来了后，会先去申请令牌，如果申请到了才会被处理，否则会阻塞或者丢弃

###### 二者区别

漏桶存储的是请求，不管当前来多少请求，都是以恒定速率发出请求

而令牌桶存储的是令牌，其放出的速率取决于当前桶中有多少令牌

>  比如，如果请求每隔五秒来一大波，假设桶的大小足够，那么实际上处理的速率是令牌生成速率的**五倍**



#### 分布式事务

###### CAP定理

<img src="http://s5cc1wj96.hd-bkt.clouddn.com/202312121501993.png" alt="image-20231212150114944" style="zoom:50%;" />

* Consistency（一致性）：不管用户访问分布式系统的哪个节点，获得的数据都必须是一样的，即使不响应也不能返回不一样的结果
* Avaliable（可用性）：不管用户访问哪个可用节点，只要访问就必须响应，即使数据不一致
* Partition tolerance（分区容错性）：集群之间出现故障导致有些实例失去连接，这就会出现独立分区。在这种情况下，仍需要对外提供服务



在CAP三个指标中，由于集群是通过网络连接的，因此P问题必须要要解决，但是

* 想达到可用性，那么就无法保证在分区情况下的数据同步问题，即失去一致性

* 想达到一致性，那么就无法保证分区情况下分区节点在做数据同步时的不可用问题，即失去可用性

故**CP和AP无法同时满足**，需要根据场景选择其中一个

###### BASE理论

BASE理论是CAP的一种解决思路

首先，要保证基本可用（Basically Available），在出现故障时，保证核心部分可用，而其余部分的可用性可以抛弃

其次，在执行过程中，允许出现软状态（Soft State），即出现临时不一致

最后，不管数据在执行时候是否一致，但最后必须要保证最终一致性（Eventually Consistency）

###### 解决方案（Seata）

<img src="http://s5cc1wj96.hd-bkt.clouddn.com/202312121525810.png" alt="image-20231212152524745" style="zoom:50%;" />

* TC（Transaction Coordinator）事务协调器：维护全局和分支事务的状态，协助全局事务的提交和回滚
* TM（Transaction Manager）事务管理器：用于开启、提交、回滚全局事务
* RM（Resource Manager）资源管理器：开启、提交、回滚分支事务，同时需要将事务执行的状态实时报告给TC

Seata有三种工作模式：XA、AT、TCC

其中XA是等待TM和TC确认提交后，才在每个RM提交事务，否则回滚，满足CP

AT则是在每个RM执行就提交，如果出现全局回滚，则使用undo log回滚，满足AP

TCC需要人工实现try、confirm、cancel操作，先全部try，所有RM都try成功才会去confirm，否则就cancel，满足AP



#### 接口幂等性

多次调用方法，不会改变业务的状态，保证重复调用和单次调用的结果一样。（比如，提交订单页面，提交多次和提交一次，最终只会下单一次）

基于restful风格的请求，GET和DELETE操作一般是幂等的，查询一定幂等，删除一般根据id删除也是幂等

而对于POST操作，可能会添加多次

对于PUT操作，如果出现类似`set stock=stcok-1`操作，那么也是不幂等的

> 解决方案的本质就是：给每次业务搞一个唯一标识，标识是否执行过就好



###### 解决方案（token+redis）

在执行逻辑之前先申请一个token，注意这两次请求需要分开，并且保证无论第二次请求重试多少次， 第一次请求只会执行一次，

<img src="http://s5cc1wj96.hd-bkt.clouddn.com/202312121601380.png" alt="image-20231212160057091" style="zoom:50%;" />

###### 解决方案（分布式锁）

创建订单之前先获取锁，一般是基于用户的一把锁，拿到锁才会创建订单，否则直接返回失败（即不需要开启重试机制）



#### 分布式任务调度

###### 路由策略

xxl-job在面对集群的情况下，只会将任务交给其中一个实例，那么分配策略就会有很多，下面给出常用的三种：

* 轮询
* 故障转移：按照顺序心跳检测，给第一个心跳检测成功的实例
* 分片广播：会广播触发所有实例执行一次任务，同时携带分片参数，每个实例根据参数执行各自的子任务 （这个适用于大数据量任务的分摊）

###### 任务执行失败

* 路由策略选择故障转移，就会使用健康的实例来执行任务
* 设置任务重试次数
* 如果还是失败了，可以查看日志并通过告警来通知开发人员