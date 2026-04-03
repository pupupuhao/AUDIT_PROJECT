<template>
  <div class="audit-container">
    <el-container>
      <el-header class="header">
        <el-icon :size="25"><ShieldCheck /></el-icon>
        <span class="title">住宅维修资金 AI 审计平台</span>
      </el-header>
      
      <el-main>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-card header="审计规则库 (PostgreSQL)">
              <el-table :data="mockRules" style="width: 100%">
                <el-table-column type="selection" width="55" />
                <el-table-column prop="label" label="条文名称" />
              </el-table>
            </el-card>
          </el-col>
          
          <el-col :span="16">
            <el-card header="报修材料上传">
              <el-upload
                drag
                action="http://localhost:8000/api/audit"
                multiple
              >
                <el-icon class="el-icon--upload"><upload-filled /></el-icon>
                <div class="el-upload__text">
                  将申请 PDF 拖到此处，或 <em>点击上传</em>
                </div>
              </el-upload>
              <el-button type="primary" style="margin-top: 20px" long>
                开始 AI 自动审计比对
              </el-button>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup lang="ts">
// 模拟数据，等你的后端 FastAPI 跑起来后，这里会换成真实的 API 调用
const mockRules = [
  { id: 1, label: '管理办法第十八条 (分摊比例)' },
  { id: 2, label: '公示流程合规性要求' },
  { id: 3, label: '第三方审价必要条件' }
]
</script>

<style scoped>
.header {
  background-color: #409EFF;
  color: white;
  display: flex;
  align-items: center;
  gap: 15px;
}
.audit-container {
  height: 100vh;
}
.title {
  font-size: 20px;
  font-weight: bold;
}
</style>