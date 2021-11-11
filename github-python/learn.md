# Super (Git) Star

## 数据准备



```python
def process(x):
    star = str2int(x['star'])
    fork = str2int(x['fork'])
    release = int(x['release'])
    contr = int(x['contributors'])
    branch = int(x['branch'])
    topic_len = len(x['topic'])
    lang_len = len(x['languages'])
    pull_open = x['pull_requests_open']
    m = re.match('(^[0-9,]+)', pull_open)
    pull_open = int(m.group(1).replace(',', ''))
    pull_clos = x['pull_requests_closed']
    m = re.match('(^[0-9,]+)', pull_clos)
    pull_clos = int(m.group(1).replace(',', ''))
    issu_open = x['issues_open']
    m = re.match('(^[0-9,]+)', issu_open)
    issu_open = int(m.group(1).replace(',', ''))
    issu_clos = x['issues_closed']
    m = re.match('(^[0-9,]+)', issu_clos)
    issu_clos = int(m.group(1).replace(',', ''))
    data = np.array([fork/1000,
                     release/10, contr,
                     pull_open/100, pull_clos/100,
                     issu_open/100, issu_clos/100]).astype(np.float32)
    lab = np.array([star]).astype(np.float32)
    return data, lab

```


## 模型定义

```python
model = model = svm.SVC(gamma=0.001, C=100.)
```

## 训练


