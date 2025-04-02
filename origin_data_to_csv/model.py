import os
import pandas as pd
import numpy as np
import torch
import ast
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split


# 自定义数据集类
class RadarDataset(Dataset):
    def __init__(self, data_dir, data_txt, max_points=30, transform=None):
        self.data_dir = data_dir
        self.max_points = max_points
        self.transform = transform
        self.samples = []
        self.data_txt = data_txt
        self.files = [line.strip() for line in open(self.data_txt, 'r')]

        # 定义动作到标签的映射（根据正负样本划分）
        self.action_mapping = {
            # 正样本
            'fanshen': 0,
            'lying': 0,
            'sit': 0,
            'leave': 0,
            # 负样本
            'roll': 1,
            'fallSit': 1,
            'slowFall': 1
        }

        # 遍历数据目录收集样本
        for filename in self.files:
            if filename.endswith('.csv'):
                # 解析文件名获取动作类型
                try:
                    action = filename.split('_')[4]  # 根据实际文件名结构调整索引
                    label = self.action_mapping[action]
                except (IndexError, KeyError):
                    continue

                # 读取CSV文件
                file_path = os.path.join(data_dir, filename)
                df = pd.read_csv(file_path)

                # 处理每一行数据
                for _, row in df.iterrows():
                    # 解析点云数据
                    point_cloud = np.array(ast.literal_eval(row[1]), dtype=np.float32)

                    # 数据预处理：标准化和填充/截断
                    processed = self.process_pointcloud(point_cloud)

                    self.samples.append((processed, label))

    def process_pointcloud(self, point_cloud):
        """预处理点云数据：标准化 + 填充/截断"""
        # 标准化（根据实际情况调整）
        point_cloud[:, :3] /= 100.0  # 归一化坐标
        point_cloud[:, 3] /= 100.0  # 归一化速度
        point_cloud[:, 4] /= 1000.0  # 归一化SNR

        # 填充/截断到固定长度
        if len(point_cloud) < self.max_points:
            pad = np.zeros((self.max_points - len(point_cloud), 5))
            point_cloud = np.concatenate([point_cloud, pad])
        else:
            point_cloud = point_cloud[:self.max_points]

        return point_cloud

    def __len__(self):
        return len(self.files)
        # return len(self.samples)

    def __getitem__(self, idx):
        point_cloud, label = self.samples[idx]
        point_cloud = torch.tensor(point_cloud, dtype=torch.float32)
        return point_cloud.permute(1, 0), torch.tensor(label, dtype=torch.long)  # (通道, 时间步)


# 示例模型1：简单时序卷积网络
class SimpleTCN(torch.nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.conv_layers = torch.nn.Sequential(
            torch.nn.Conv1d(5, 16, kernel_size=3, padding=1),
            torch.nn.ReLU(),
            torch.nn.MaxPool1d(2),
            torch.nn.Conv1d(16, 32, kernel_size=3, padding=1),
            torch.nn.ReLU(),
            torch.nn.AdaptiveAvgPool1d(1)
        )
        self.classifier = torch.nn.Sequential(
            torch.nn.Linear(32, 16),
            torch.nn.ReLU(),
            torch.nn.Linear(16, num_classes))

    def forward(self, x):
        x = self.conv_layers(x)
        x = x.view(x.size(0), -1)
        return self.classifier(x)


# 示例模型2：轻量级点云处理网络
class PointNetMini(torch.nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.mlp = torch.nn.Sequential(
            torch.nn.Linear(5, 16),
            torch.nn.ReLU(),
            torch.nn.Linear(16, 32)
        )
        self.pool = torch.nn.AdaptiveMaxPool1d(1)
        self.classifier = torch.nn.Sequential(
            torch.nn.Linear(32, 16),
            torch.nn.ReLU(),
            torch.nn.Linear(16, num_classes))

    def forward(self, x):
        x = self.mlp(x.permute(0, 2, 1))  # (batch, channels, features)
        x = self.pool(x).squeeze(-1)
        return self.classifier(x)


# 示例模型3：混合模型
class HybridModel(torch.nn.Module):
    def __init__(self, num_classes=2):
        super().__init__()
        self.tcn = torch.nn.Sequential(
            torch.nn.Conv1d(5, 16, 3, padding=1),
            torch.nn.ReLU(),
            torch.nn.MaxPool1d(2),
            torch.nn.Conv1d(16, 32, 3, padding=1),
            torch.nn.ReLU()
        )
        self.rnn = torch.nn.GRU(32, 16, batch_first=True)
        self.classifier = torch.nn.Linear(16, num_classes)

    def forward(self, x):
        x = self.tcn(x)
        x = x.permute(0, 2, 1)  # (batch, seq_len, features)
        _, h_n = self.rnn(x)
        return self.classifier(h_n[-1])


# 数据加载示例
if __name__ == "__main__":
    # 参数设置
    DATA_DIR = "your_data_directory"
    BATCH_SIZE = 32
    MAX_POINTS = 30

    # 创建数据集和数据加载器
    dataset = RadarDataset(DATA_DIR, max_points=MAX_POINTS)
    train_set, val_set = train_test_split(dataset, test_size=0.2)

    train_loader = DataLoader(train_set, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_set, batch_size=BATCH_SIZE)

    # 模型初始化
    model = SimpleTCN(num_classes=2)
    criterion = torch.nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)

    # 简单训练循环示例
    for epoch in range(10):
        model.train()
        for inputs, labels in train_loader:
            outputs = model(inputs)
            loss = criterion(outputs, labels)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        # 验证
        model.eval()
        total = 0
        correct = 0
        with torch.no_grad():
            for inputs, labels in val_loader:
                outputs = model(inputs)
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()

        print(f"Epoch {epoch + 1}, Val Acc: {correct / total:.2f}")