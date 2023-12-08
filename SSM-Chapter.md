## 框架篇（SSM）

#### Bean的线程安全问题

在Spring中，bean默认是单例的。但是一旦bean中包含可修改的成员变量，那么这个bean就不是线程安全的。



#### AOP

AOP成为面向切面编程，可以用来抽取多个方法、对象的通用操作封装成一个独立模块，减少代码的耦合度以及冗余度。

常见的AOP使用场景有：记录操作日志（数据库操作、接口访问操作等）、缓存处理（`@Cachable`）、事务处理（`@Transactional`）

Spring中的事务就是通过@Transactional注解实现的，其本质是一个环绕类型的AOP，在执行前开启事务，执行后提交事务，如果catch到异常就会回滚事务。

```java
@Component
@Aspect
@Slf4j
public class LogAspect {
    @Pointcut("execution(* com.zenith.controller.*.* (..))")
    public void pt(){
    }

    @Around("pt()")
    public Object handlerController(ProceedingJoinPoint joinPoint){
        Object res=null;
        RequestAttributes ra = RequestContextHolder.getRequestAttributes();
        ServletRequestAttributes sra = (ServletRequestAttributes) ra;
        HttpServletRequest request = sra.getRequest();

        String serverName = request.getServerName();
        String pathInfo = request.getServletPath();
        String method = request.getMethod();
        log.debug("From server: {}, request =>[{} {}]",serverName,method,pathInfo);

        try {
            long begin = System.currentTimeMillis();
            res=joinPoint.proceed();
            long end=System.currentTimeMillis();
            log.debug("[{} {}] request successfully, runtime {} ms",method,pathInfo, end-begin);
        } catch (Throwable throwable) {
            throwable.printStackTrace();
            log.error("[{} {}] request failed!",method,pathInfo);
        }
        return res;
    }
}
```



#### 事务失效

**异常捕获处理**

在事务中捕获异常没有抛出，而是在catch中自己处理了。由于事务的AOP中就无法捕获到异常，会直接提交事务，导致不一致性。

解决方法：在catch中手动抛出异常

**抛出检查异常**

如果在方法后面加上throw 异常，那么就不会抛出RuntimeException了，而spring的事务AOP默认只会捕获运行时异常。

解决方法：在`@Transactional`注解中指定捕获的异常类

**非public方法**

如果使用注解的方法不是public方法，那么也会失效。

解决方法：加上public

**在Bean内部调用自己的事务方法**

由于在内部调用自己的方法，因此没有使用代理类，导致AOP失效。

解决方法：在方法内部注入自己，用这个类调用方法。



#### Bean的生命周期

<img src="https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231207163100469.png" alt="image-20231207163100469" style="zoom: 50%;" />

* 执行构造函数实例化bean
* bean依赖注入
* 处理一系列Aware结尾的接口
* 执行bean的前置处理器
* 初始化方法（PostConstruct自定义初始化、内置的初始化）
* 执行bean的后置处理器，一般在这做AOP，动态代理
* 销毁bean



#### 循环引用

**产生原因**

如果bean对象之间的依赖注入关系形成一个环，就说明存在循环引用

具体产生过程如下图

<img src="https://raw.githubusercontent.com/ZenithWon/figure/master/202312081009250.png" alt="image-20231208092612729" style="zoom:50%;" />

**三级缓存**

Spring是通过三级缓存解决循环依赖的：

* 一级缓存：单例池，缓存已经初始化完的bean对象
* 二级缓存：缓存早期的bean对象，还没有执行完初始化的生命周期，比如没有依赖注入
* 三级缓存：缓存对象工厂，用来构造相应的对象

**解决方法**

当需要依赖注入的时候，先去单例池中找，再去二级缓存中找这样只要这个bean执行了构造函数，就不会出现在依赖注入时再次构造该对象的情况，打破了环。

<img src="https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231208094441975.png" alt="image-20231208094441975" style="zoom:50%;" />

若需要注入的是一个代理对象，那么仅通过二级缓存还是无法解决，因为二级缓存注入的永远是对象本身，因此需要借助三级缓存的对象工厂生成代理对象。

<img src="https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231208094721969.png" alt="image-20231208094721969" style="zoom:50%;" />

> 注意上述的前提是执行了构造函数才可以打破循环依赖，如果通过构造函数注入，还是无法解决，那么可以在构造函数的bean对象前面加上一个`@Lazy`的注解，就可以实现懒加载，需要的时候才会注入，保证该对象的构造函数已经执行。



#### SpringMVC执行流程

**视图阶段**

<img src="https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231207165810673.png" alt="image-20231207165810673" style="zoom:50%;" />

**前后端分离阶段**

如果加上了`@reponsebody`注解

<img src="https://raw.githubusercontent.com/ZenithWon/figure/master/image-20231207165835812.png" alt="image-20231207165835812" style="zoom: 50%;" />



#### Springboot自动配置

springboot的自动配置主要就是依赖于启动类上的`@SpringBootApplication`注解，这个注解包含三个注解：

* `@SpringBootConfiguration`：和`@Configuration`注解是一个意思，表明这个类是一个配置类
* `@ComponentScan`：扫描组件，默认是当前类所在的包以及子包
* `@EnableAutoConfiguration`：这个是SpringBoot开启自动配置的核心注解

**EnableAutoConfiguration**

在这个注解中会import了一个AutoConfigurationImportSelector，这个类会加载一个文件spring.factories，这个文件记录了许多自动配置类，比如RedisAutoConfiguration这种，这些自动配置中会自动加载该相关的所有bean对象

在项目启动时，会逐一加载这些自动配置，但是并不是会将其中定义的所有并对象加载，他会在加载前根据`@ConditionalOnClass`注解判断是否引入了相应的spring-boot-starter-xxx。如果在项目中引入了，那么就会将该文件中的相关类全部放到容器中加载所有bean对象，实现自动配置。

当然，在加载bean对象之前会先查看容器中是否存在（即用户是否自己定义了），如果定义了就不会导入了

> 在spring项目中一般import都是导入了某一个东西，由于ComponentScan默认只扫描所在包以及子包，因此为了是不属于当前项目的模块生效，一般就是直接import进来，放到容器中管理。



#### Mybatis执行流程

<img src="https://raw.githubusercontent.com/ZenithWon/figure/master/202312081050829.png" alt="202312081050829" style="zoom: 50%;" />

* 加载配置文件，里面包含数据库的配置、映射文件配置等

* 通创建SqlSessionFactory会话工厂对象，每执行一个操作就会创建SqlSession
* SqlSession会通过Excutor执行器操作数据库，并且Excutor会负责缓存维护
* 在Excutor前会通过MappedStatement读取xml文件中的sql信息，才能执行对应的sql语句
* 并且在执行语句的之前和之后都会处理输入输出参数，在数据库和Java之间转换



#### Mybatis的缓存

用于保存查询的历史记录，下次查询就不需要再去查询数据库了

Mybatis有两级缓存

* 一级缓存：保存本次sqlSession的数据，如果sqlSession执行了close或者flush函数，那么就会重置缓存
* 二级缓存：保存mapper的所有数据，即使不是一个会话，也会保存

Mybatis默认只开启一级缓存，在MybatisPlus中开启需要：

* 在application.yml文件中设置cache-enabled为true
* 在对于的Mapper上面添加`@CacheNamespace`注解

> 注意：发生写操作，缓存会被清空