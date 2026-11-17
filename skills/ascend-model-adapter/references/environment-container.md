# Ascend 容器环境参考

用于准备真实运行环境时按需读取。以下保留已有开发容器模板；它包含 root、privileged 和 host 共享，仅适用于明确需要这些权限的可信开发环境。它不能作为不可信代码的隔离保证。

处理不可信仓库/权重时先审计安装、下载和加载逻辑，使用受控环境；只开放必要设备、权限、网络与目录。不要直接复用完整缓存挂载。将调整后的实际镜像 digest、软件栈和设备配置记入内部证据；README 只保留使用者复现所需命令。

```bash
export IMAGE=<ascend-image-tag>
docker pull ${IMAGE}

docker run -itd -u root --net=host --privileged=true \
  --name <container-name> \
  --shm-size=256g \
  --ipc=host \
  --device=/dev/davinci0 \
  --device=/dev/davinci_manager \
  --device=/dev/devmm_svm \
  --device=/dev/hisi_hdc \
  -v /usr/local/Ascend/driver:/usr/local/Ascend/driver \
  -v /usr/local/Ascend/firmware:/usr/local/Ascend/firmware:ro \
  -v /usr/local/dcmi:/usr/local/dcmi \
  -v /usr/local/sbin/npu-smi:/usr/local/sbin/npu-smi \
  -v /etc/ascend_install.info:/etc/ascend_install.info \
  -v <宿主机工程目录>:<宿主机工程目录> \
  -v /root/.cache:/root/.cache \
  ${IMAGE} bash -i

docker exec -it <container-name> bash
cd <宿主机工程目录>
source /usr/local/Ascend/ascend-toolkit/set_env.sh
npu-smi info
python3 -c "import torch, torch_npu; print(torch.__version__, torch_npu.__version__, torch.npu.is_available())"
```

多卡时增加实际需要的 `/dev/davinci*`。镜像 tag 与目标硬件/CANN 栈必须成套；能获取 digest 时把 digest 记入项目证据。
