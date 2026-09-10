# Model Specification v0.1

## Q1：有界角误差的交会定位

### 1. 集合与变量

第 i 个检测点：S_i=(x_i,y_i)。测得示向度 theta_i，误差半宽 delta=1°。

定义单位向量 u(phi)=(cos phi, sin phi)。真实源点 G 必须位于从 S_i 出发、方向区间 [theta_i-delta, theta_i+delta] 的前向楔形 W_i 内。

对 lower=theta_i-delta, upper=theta_i+delta，有：

cross(u(lower), G-S_i) >= 0,
cross(u(upper), G-S_i) <= 0。

两式均为线性半平面，因此 P=intersection_i W_i 为凸集。

### 2. 顶点算法

将所有 2n 条边界写成 A_j x + B_j y <= C_j。
对每一对非平行边界求交点 v；若 v 满足全部半平面，则保留。去重后按极角/凸包顺序排列，即得到有界定位多边形顶点。

额外状态：
- 无任何可行点且约束矛盾：EMPTY；
- 存在非零 recession direction d 满足 A_j d_x+B_j d_y<=0 对所有 j：UNBOUNDED；
- 否则 BOUNDED。

### 3. 直径

若 P 顶点为 v_1,...,v_m，凸集直径一定在极点取得：

D=max_{j,k} ||v_j-v_k||。

规模很小时 O(m^2) 足够；若需要可替换为 rotating calipers O(m)。

### 4. “直径为D的圆”覆盖判据

取任意一对直径点 a,b，||a-b||=D。若一个半径 D/2 的圆同时覆盖 a,b，则圆心被唯一迫使为 c=(a+b)/2。故存在直径为D的覆盖圆，当且仅当

max_{v in vertices(P)} ||v-c|| <= D/2。

因此答案是：**不一定能覆盖**。例如等边三角形边长D的最小覆盖圆半径为 D/sqrt(3)>D/2。

---

## Q2：第二检测点主动设计

### 1. 第一次可行源集合

全向源给出示向度时，距离必 >5 m，且因有效接收半径 <=1500 m，源点还满足 ||G-S1||<=1500。再结合目标圆：

Omega1 = target_disk ∩ W(S1,theta1,delta) ∩ {5<||G-S1||<=1500}。

### 2. 几何信息量

对候选 S2 与假设源点 G，定义两条视线的交会角 alpha in [0,pi/2]（取无向锐角）。

q_angle=sin^2(alpha)。

其理由：两测向线近似平行时误差区沿交会方向被放大，局部不确定度与 1/|sin alpha| 成正比；90° 附近最佳。

### 3. 探测鲁棒项

由于所有全向源接收半径至少1000 m，若 ||S2-G||<=1000，则第二点一定可收到信号。因此：

q_det(G,S2)=1[||S2-G||<=1000]。

### 4. 移动代价

q_move=||S2-S1||/1000。

### 5. 主评分

在 Omega1 的离散样本 G_k 上：

J(S2)=mean_k(q_det*q_angle)-lambda*q_move。

同时报告：
- guarantee_rate = mean_k(q_det)
- angle_q10 / angle_median
- 预计二测后定位区域直径。

推荐点先满足 guarantee_rate>=p0，再最大化 J；若不存在则按 Pareto 前沿选择。

### 6. 候选区域

数值上构造：

C={S2: d(S2,S1)<=Lmax, guarantee_rate>=p0, angle_q10>=alpha_min}。

初始建议 Lmax=1000 m、p0=0.80、alpha_min=30°，仅作为可调实验参数，不写成题面事实。几何 baseline 候选区是围绕第一可行段中点 Ghat 的法向带：

|angle(S2-Ghat, Ghat-S1)-90°|<=30°,
||S2-Ghat||<=1000。

---

## Q3：全向源在线状态机

### TargetState

每个频道 ch 维护：UNKNOWN / DETECTED / LOCALIZING / CLEARED / PROVED_ABSENT。

附加字段：measurements、current_polygon、recommended_clear_center、last_seen、failed_clear_positions。

### 全局覆盖哨点 baseline

使用 center + 6 ring 点。若环半径 a 满足边界最坏角差30°处到最近环点<=1000：

1800^2+a^2-2*1800*a*cos30° <=1000^2。

为缩短移动，取较小根：

a*=1800 cos30°-sqrt(1000^2-1800^2 sin^2 30°) ≈1122.96 m。

则中心负责 rho<=1000，六个环点负责 1000<=rho<=1800 的每个方向，形成全向源最小接收半径下的确定性覆盖 baseline。

### 清除触发

若定位多边形 P 的某个候选中心 c 使 max_{v in vertices(P)}||v-c||<=20，则发送 /clear(c,ch)。可先测试直径对中点、MEC中心或Chebyshev center近似。

### 调度目标

每个候选动作 a 估计

score(a)=expected_information_or_clear_gain / expected_virtual_time。

在必须完成尚未证明频道的覆盖扫描这一硬约束下，允许对已发现目标插入高收益定位/清除动作。

---

## Q4：定向源方向鲁棒发现

定向覆盖可写为：存在未知单位方向 d，使检测点 S 满足

||S-G||<=R_G,
d·(S-G)>=0。

若 G 属于三角形 conv{A,B,C}，且 |GA|,|GB|,|GC|<=1000，则 G=sum lambda_i V_i，lambda_i>=0, sum lambda_i=1。
若假设三点都在盲半平面，则 d·(V_i-G)<0 对全部 i，按凸组合求和得到 0<0 的矛盾。因此至少一顶点可见。

由此得到网格设计条件：用边长 s<=1000 的三角剖分覆盖整个目标圆（边界允许顶点在圆外），并对仍未知频道扫描相应顶点。
