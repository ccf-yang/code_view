document.addEventListener('DOMContentLoaded', function() {
    const projectPath = document.getElementById('projectPath');
    const inputType = document.getElementById('inputType');
    const refreshBtn = document.getElementById('refreshBtn');
    const historyBtn = document.getElementById('historyBtn');
    const historyDropdown = document.getElementById('historyDropdown');
    const selectWrapper = historyBtn.parentElement;
    const fileList = document.getElementById('fileList');
    const fileContent = document.getElementById('fileContent');
    const aiBtn = document.getElementById('aiBtn');
    const saveAiBtn = document.getElementById('saveAiBtn');
    const aiResult = document.getElementById('aiResult');
    const notification = document.getElementById('notification');
    const modelSelect = document.getElementById('modelSelect');
    const currentFile = document.getElementById('currentFile');
    
    let currentFilePath = '';
    let lastSavedAnalysis = '';
    let notificationTimeout;

    // Load history function
    async function loadHistory() {
        try {
            const response = await fetch('http://localhost:8000/api/history');
            if (!response.ok) {
                throw new Error('Failed to load history');
            }
            const data = await response.json();
            
            // Clear existing items
            historyDropdown.innerHTML = '';
            
            // Filter history based on current input type
            const currentType = inputType.value;
            const filteredHistory = data.history.filter(path => {
                if (currentType === 'git') {
                    return path.startsWith('http://') || path.startsWith('https://') || path.startsWith('git://');
                } else {
                    return !path.startsWith('http://') && !path.startsWith('https://') && !path.startsWith('git://');
                }
            });
            
            if (filteredHistory.length === 0) {
                const emptyDiv = document.createElement('div');
                emptyDiv.className = 'history-option';
                emptyDiv.style.justifyContent = 'center';
                emptyDiv.style.color = '#666';
                emptyDiv.textContent = '暂无历史记录';
                historyDropdown.appendChild(emptyDiv);
                return;
            }
            
            // Add history items
            filteredHistory.forEach(path => {
                const div = document.createElement('div');
                div.className = 'history-option';
                
                const pathSpan = document.createElement('span');
                pathSpan.textContent = path;
                pathSpan.style.flex = '1';
                pathSpan.style.overflow = 'hidden';
                pathSpan.style.textOverflow = 'ellipsis';
                div.appendChild(pathSpan);
                
                const deleteBtn = document.createElement('span');
                deleteBtn.className = 'delete-btn';
                deleteBtn.textContent = '×';
                deleteBtn.onclick = async (e) => {
                    e.stopPropagation();
                    try {
                        const response = await fetch('http://localhost:8000/api/history', {
                            method: 'DELETE',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ path })
                        });
                        
                        if (!response.ok) {
                            throw new Error('Failed to delete history item');
                        }
                        
                        div.remove();
                        if (historyDropdown.children.length === 0) {
                            const emptyDiv = document.createElement('div');
                            emptyDiv.className = 'history-option';
                            emptyDiv.style.justifyContent = 'center';
                            emptyDiv.style.color = '#666';
                            emptyDiv.textContent = '暂无历史记录';
                            historyDropdown.appendChild(emptyDiv);
                        }
                        showNotification('历史记录已删除');
                    } catch (error) {
                        console.error('Error deleting history:', error);
                        showNotification('删除历史记录失败', true);
                    }
                };
                div.appendChild(deleteBtn);
                
                div.onclick = () => {
                    projectPath.value = path;
                    // Copy to clipboard
                    navigator.clipboard.writeText(path)
                        .then(() => {
                            showNotification('路径已复制到剪贴板');
                            selectWrapper.classList.remove('open');
                        })
                        .catch(() => {
                            showNotification('复制到剪贴板失败', true);
                        });
                };
                
                historyDropdown.appendChild(div);
            });
        } catch (error) {
            console.error('Error loading history:', error);
            showNotification('加载历史记录失败', true);
        }
    }

    // Toggle dropdown
    historyBtn.addEventListener('click', function(e) {
        e.stopPropagation();  // 阻止事件冒泡
        if (!selectWrapper.classList.contains('open')) {
            loadHistory();
        }
        selectWrapper.classList.toggle('open');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(e) {
        if (!selectWrapper.contains(e.target)) {
            selectWrapper.classList.remove('open');
        }
    });

    // Update input placeholder based on selected type
    inputType.addEventListener('change', function() {
        if (this.value === 'local') {
            projectPath.placeholder = '请输入本地目录路径，例如：D:/projects/mycode';
            refreshBtn.textContent = '加载项目';
        } else {
            projectPath.placeholder = '请输入Git仓库地址，例如：https://github.com/username/repo';
            refreshBtn.textContent = '克隆并加载';
        }
        // Reload history when type changes
        if (selectWrapper.classList.contains('open')) {
            loadHistory();
        }
    });

    // Show notification function
    function showNotification(message, isError = false) {
        // Clear any existing timeout
        if (notificationTimeout) {
            clearTimeout(notificationTimeout);
            notification.classList.remove('show');
        }

        // Set message and show notification
        notification.textContent = message;
        notification.classList.toggle('error', isError);
        notification.classList.add('show');

        // Hide after 2 seconds
        notificationTimeout = setTimeout(() => {
            notification.classList.remove('show');
        }, 2000);
    }

    // Load files when refresh button is clicked
    refreshBtn.addEventListener('click', async () => {
        const path = projectPath.value.trim();
        if (!path) {
            showNotification('请输入' + (inputType.value === 'local' ? '项目目录路径' : 'Git仓库地址'), true);
            return;
        }

        try {
            fileList.innerHTML = '';
            let finalPath = path;

            if (inputType.value === 'git') {
                // Clone repository if it's a Git URL
                const response = await fetch('http://localhost:8000/api/clone-repo', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ url: path })
                });

                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Failed to clone repository');
                }

                const result = await response.json();
                finalPath = result.path;
            }

            // Load files using the local path
            const filesResponse = await fetch(`http://localhost:8000/api/files?path=${encodeURIComponent(finalPath)}&should_save_history=true`);
            if (!filesResponse.ok) {
                throw new Error('Failed to load files');
            }
            const files = await filesResponse.json();
            displayFiles(files, fileList, 0);
            showNotification(inputType.value === 'git' ? '仓库克隆并加载成功' : '项目加载成功');
        } catch (error) {
            console.error('Error:', error);
            showNotification(error.message || '操作失败，请检查后重试', true);
        }
    });

    // Display files in the file list
    function displayFiles(files, parentElement, level) {
        files.forEach(file => {
            // Skip .ai files
            if (!file.isDirectory && file.name.endsWith('.ai')) {
                return;
            }

            const fileItem = document.createElement('div');
            fileItem.className = 'file-item';
            fileItem.style.paddingLeft = `${level * 20}px`;
            
            if (file.isDirectory) {
                const toggleBtn = document.createElement('span');
                toggleBtn.className = 'toggle-btn';
                toggleBtn.textContent = '▶';
                toggleBtn.style.marginRight = '5px';
                fileItem.appendChild(toggleBtn);

                const dirName = document.createElement('span');
                dirName.textContent = file.name + '/';
                fileItem.appendChild(dirName);

                const contentDiv = document.createElement('div');
                contentDiv.className = 'directory-content';
                contentDiv.style.display = 'none';

                let isLoaded = false;

                // 移除单独的toggleBtn点击事件，改为整行点击
                fileItem.style.cursor = 'pointer';
                fileItem.addEventListener('click', async (e) => {
                    const isExpanded = toggleBtn.textContent === '▼';
                    toggleBtn.textContent = isExpanded ? '▶' : '▼';
                    contentDiv.style.display = isExpanded ? 'none' : 'block';

                    if (!isLoaded && !isExpanded) {
                        try {
                            const response = await fetch(`http://localhost:8000/api/files?path=${encodeURIComponent(file.path)}`);
                            if (!response.ok) {
                                throw new Error('Failed to load subdirectory');
                            }
                            const subFiles = await response.json();
                            displayFiles(subFiles, contentDiv, level + 1);
                            isLoaded = true;
                        } catch (error) {
                            console.error('Error loading subdirectory:', error);
                            showNotification('加载子目录失败', true);
                        }
                    }
                });

                parentElement.appendChild(fileItem);
                parentElement.appendChild(contentDiv);
            } else {
                fileItem.textContent = file.name;
                fileItem.style.cursor = 'pointer';
                fileItem.addEventListener('click', () => loadFile(file.path));
                parentElement.appendChild(fileItem);
            }
        });
    }

    // Load file content and its analysis if exists
    async function loadFile(filePath) {
        try {
            currentFilePath = filePath;
            currentFile.textContent = `当前文件：${filePath}`;
            
            // Load file content
            const contentResponse = await fetch(`http://localhost:8000/api/content?path=${encodeURIComponent(filePath)}`);
            if (!contentResponse.ok) {
                throw new Error('Failed to load file content');
            }
            const contentData = await contentResponse.json();
            
            // 创建 pre 和 code 元素用于语法高亮
            const pre = document.createElement('pre');
            const code = document.createElement('code');
            
            // 根据文件扩展名设置语言
            const ext = filePath.split('.').pop().toLowerCase();
            const languageMap = {
                'js': 'javascript',
                'py': 'python',
                'html': 'html',
                'css': 'css',
                'json': 'json',
                'md': 'markdown',
                'txt': 'plaintext',
                'go': 'go'
            };
            
            if (languageMap[ext]) {
                code.classList.add(`language-${languageMap[ext]}`);
            }
            
            // 设置代码内容
            code.textContent = contentData.content;
            pre.appendChild(code);
            
            // 清空并添加新内容
            fileContent.innerHTML = '';
            fileContent.appendChild(pre);
            
            // 等待 DOM 更新后应用高亮
            setTimeout(() => {
                hljs.highlightElement(code);
            }, 0);

            // Try to load existing analysis
            try {
                const analysisResponse = await fetch(`http://localhost:8000/api/load_analysis?path=${encodeURIComponent(filePath)}`);
                if (analysisResponse.ok) {
                    const analysisData = await analysisResponse.json();
                    
                    // 使用 marked 渲染 Markdown
                    aiResult.innerHTML = marked.parse(analysisData.content);
                    
                    lastSavedAnalysis = analysisData.content;
                    showNotification('文件及分析加载完成');
                } else {
                    aiResult.innerHTML = '';
                    lastSavedAnalysis = '';
                    showNotification('文件加载完成');
                }
            } catch (error) {
                console.error('Error loading analysis:', error);
                aiResult.textContent = '';
                lastSavedAnalysis = '';
                showNotification('加载分析失败', true);
            }
        } catch (error) {
            console.error('Error loading file:', error);
            showNotification('加载文件失败', true);
        }
    }

    // AI Analysis button click handler
    aiBtn.addEventListener('click', async () => {
        const content = fileContent.textContent;
        const selectedModel = modelSelect.value;
        
        if (!content || !currentFilePath) {
            showNotification('请先选择一个文件', true);
            return;
        }

        try {
            aiResult.textContent = '正在分析代码...';
            const response = await fetch('http://localhost:8000/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    code: content,
                    model: selectedModel,
                    stream: false
                })
            });

            if (!response.ok) {
                throw new Error('Failed to analyze code');
            }

            const result = await response.json();
            
            // 使用 marked 渲染 Markdown
            aiResult.innerHTML = marked.parse(result.content);
            
            lastSavedAnalysis = result.content;
            showNotification('代码分析完成，如需保存请点击保存按钮');
        } catch (error) {
            console.error('Error during AI analysis:', error);
            aiResult.textContent = '分析代码时出错: ' + error.message;
            showNotification('代码分析失败', true);
        }
    });

    // Save AI Analysis button click handler
    saveAiBtn.addEventListener('click', saveAnalysis);

    // Save analysis function
    async function saveAnalysis() {
        if (!currentFilePath) {
            showNotification('请先选择一个文件', true);
            return;
        }

        if (!lastSavedAnalysis.trim()) {
            showNotification('没有可保存的分析内容', true);
            return;
        }

        try {
            const response = await fetch('http://localhost:8000/api/save_analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    path: currentFilePath,
                    content: lastSavedAnalysis
                })
            });

            if (!response.ok) {
                throw new Error('Failed to save analysis');
            }

            showNotification('分析保存成功');
        } catch (error) {
            console.error('Error saving analysis:', error);
            showNotification('保存分析失败', true);
        }
    }

    // Add ctrl+s save handler for AI result
    document.addEventListener('keydown', async (e) => {
        if (e.ctrlKey && e.key === 's' && document.activeElement === aiResult) {
            e.preventDefault();
            await saveAnalysis();
        }
    });
});
