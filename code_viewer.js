document.addEventListener('DOMContentLoaded', function() {
    const projectPath = document.getElementById('projectPath');
    const inputType = document.getElementById('inputType');
    const refreshBtn = document.getElementById('refreshBtn');
    const fileList = document.getElementById('fileList');
    const fileContent = document.getElementById('fileContent');
    const aiBtn = document.getElementById('aiBtn');
    const saveAiBtn = document.getElementById('saveAiBtn');
    const aiResult = document.getElementById('aiResult');
    const notification = document.getElementById('notification');
    const modelSelect = document.getElementById('modelSelect'); // Assuming this element exists
    const currentFile = document.getElementById('currentFile');
    
    let currentFilePath = '';  // Store current file path
    let lastSavedAnalysis = ''; // Store last saved analysis content
    let notificationTimeout;

    // Update input placeholder based on selected type
    inputType.addEventListener('change', function() {
        if (this.value === 'local') {
            projectPath.placeholder = '请输入本地目录路径，例如：D:/projects/mycode';
            refreshBtn.textContent = '加载项目';
        } else {
            projectPath.placeholder = '请输入Git仓库地址，例如：https://github.com/username/repo';
            refreshBtn.textContent = '克隆并加载';
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

        if (inputType.value === 'git') {
            showNotification('Git仓库克隆功能即将推出，敬请期待！');
            return;
        }
        
        try {
            fileList.innerHTML = '';
            const response = await fetch(`http://localhost:8000/api/files?path=${encodeURIComponent(path)}`);
            if (!response.ok) {
                throw new Error('Failed to load files');
            }
            const files = await response.json();
            displayFiles(files, fileList, 0);
            showNotification('项目加载成功');
        } catch (error) {
            console.error('Error loading files:', error);
            showNotification('加载项目失败，请检查路径后重试', true);
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
            fileContent.textContent = contentData.content;

            // Try to load existing analysis
            try {
                const analysisResponse = await fetch(`http://localhost:8000/api/load_analysis?path=${encodeURIComponent(filePath)}`);
                if (analysisResponse.ok) {
                    const analysisData = await analysisResponse.json();
                    aiResult.textContent = analysisData.content;
                    lastSavedAnalysis = analysisData.content;
                    showNotification('文件及分析加载完成');
                } else {
                    aiResult.textContent = '';
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
            aiResult.textContent = result.content;
            lastSavedAnalysis = result.content;

            // Automatically save the new analysis
            // await saveAnalysis();
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

        const currentAnalysis = aiResult.textContent;
        if (!currentAnalysis.trim()) {
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
                    content: currentAnalysis
                })
            });

            if (!response.ok) {
                throw new Error('Failed to save analysis');
            }

            lastSavedAnalysis = currentAnalysis;
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
