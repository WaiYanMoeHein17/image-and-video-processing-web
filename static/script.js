// FilmMaster & ImagePro - Professional Media Processing JavaScript

class MediaProcessor {
    constructor() {
        this.currentFile = null;
        this.currentFileType = null;
        this.appliedOperations = [];
        this.availableOperations = [];
        this.useWASM = false;
        this.wasmModule = null;
        this.videoBuffer = null;
        
        this.initializeElements();
        this.bindEvents();
        this.loadOperations();
    }
    
    initializeElements() {
        // Upload elements
        this.uploadArea = document.getElementById('uploadArea');
        this.fileInput = document.getElementById('fileInput');
        this.uploadProgress = document.getElementById('uploadProgress');
        this.progressFill = document.getElementById('progressFill');
        this.progressText = document.getElementById('progressText');
        
        // Preview elements
        this.previewSection = document.getElementById('previewSection');
        this.mediaTitle = document.getElementById('mediaTitle');
        this.originalContainer = document.getElementById('originalContainer');
        this.processedContainer = document.getElementById('processedContainer');
        this.resetBtn = document.getElementById('resetBtn');
        
        // Controls elements
        this.controlsSection = document.getElementById('controlsSection');
        this.controlsTitle = document.getElementById('controlsTitle');
        this.mediaTypeBadge = document.getElementById('mediaTypeBadge');
        this.processingModeBadge = document.getElementById('processingModeBadge');
        this.addOperationBtn = document.getElementById('addOperationBtn');
        this.operationsList = document.getElementById('operationsList');
        this.appliedList = document.getElementById('appliedList');
        this.operationCount = document.getElementById('operationCount');
        this.processBtn = document.getElementById('processBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
        
        // Processing elements
        this.processingOverlay = document.getElementById('processingOverlay');
        this.processingStatus = document.getElementById('processingStatus');
        this.processingProgressFill = document.getElementById('processingProgressFill');
        
        // Modal elements
        this.operationModal = document.getElementById('operationModal');
        this.modalTitle = document.getElementById('modalTitle');
        this.modalClose = document.getElementById('modalClose');
        this.operationSelect = document.getElementById('operationSelect');
        this.operationDescription = document.getElementById('operationDescription');
        this.operationParams = document.getElementById('operationParams');
        this.modalCancel = document.getElementById('modalCancel');
        this.modalAdd = document.getElementById('modalAdd');
    }
    
    bindEvents() {
        // Upload events
        this.uploadArea.addEventListener('click', () => this.fileInput.click());
        this.uploadArea.addEventListener('dragover', this.handleDragOver.bind(this));
        this.uploadArea.addEventListener('dragleave', this.handleDragLeave.bind(this));
        this.uploadArea.addEventListener('drop', this.handleDrop.bind(this));
        this.fileInput.addEventListener('change', this.handleFileSelect.bind(this));
        this.resetBtn.addEventListener('click', this.resetApplication.bind(this));
        
        // Controls events
        this.addOperationBtn.addEventListener('click', this.showOperationModal.bind(this));
        this.processBtn.addEventListener('click', this.processMedia.bind(this));
        this.downloadBtn.addEventListener('click', this.downloadResult.bind(this));
        
        // Modal events
        this.modalClose.addEventListener('click', this.hideOperationModal.bind(this));
        this.modalCancel.addEventListener('click', this.hideOperationModal.bind(this));
        this.modalAdd.addEventListener('click', this.addOperation.bind(this));
        this.operationSelect.addEventListener('change', this.updateOperationInfo.bind(this));
        
        // Close modal when clicking outside
        this.operationModal.addEventListener('click', (e) => {
            if (e.target === this.operationModal) {
                this.hideOperationModal();
            }
        });
    }
    
    handleDragOver(e) {
        e.preventDefault();
        this.uploadArea.classList.add('dragover');
    }
    
    handleDragLeave(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
    }
    
    handleDrop(e) {
        e.preventDefault();
        this.uploadArea.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.handleFile(files[0]);
        }
    }
    
    handleFileSelect(e) {
        const files = e.target.files;
        if (files.length > 0) {
            this.handleFile(files[0]);
        }
    }
    
    async handleFile(file) {
        // Determine processing mode based on file size
        const fileSizeMB = file.size / (1024 * 1024);
        const useWASM = fileSizeMB > 50 && file.type.startsWith('video/');
        
        console.log(`File size: ${fileSizeMB.toFixed(2)}MB, Using WASM: ${useWASM}`);
        
        // Show upload progress (skip for WASM processing)
        if (!useWASM) {
            this.showUploadProgress();
        }        try {
            if (useWASM) {
                // Handle WASM processing (no upload needed)
                await this.handleWASMFile(file);
            } else {
                // Handle server-side processing (upload required)
                const response = await this.uploadFile(file);
                
                if (response.success) {
                    this.currentFile = response;
                    this.currentFileType = response.file_type;
                    this.useWASM = false;
                    this.displayMedia(file, response.file_type);
                    this.showControls(response.file_type);
                    this.loadOperations();
                } else {
                    this.showError(response.error || 'Upload failed');
                }
            }
        } catch (error) {
            this.showError('Processing failed: ' + error.message);
        } finally {
            if (!useWASM) {
                this.hideUploadProgress();
            }
        }
    }
    
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        return await response.json();
    }
    
    async handleWASMFile(file) {
        // Set WASM mode
        this.useWASM = true;
        this.currentFile = { file_id: 'wasm_' + Date.now(), filename: file.name };
        this.currentFileType = 'video';
        
        // Load WASM module if not already loaded
        if (!this.wasmModule) {
            await this.loadWASMModule();
        }
        
        // Convert video file to buffer for WASM processing
        this.videoBuffer = await this.fileToArrayBuffer(file);
        
        // Display media and controls
        this.displayMedia(file, 'video');
        this.showControls('video');
        this.loadOperations();
    }
    
    async loadWASMModule() {
        try {
            console.log('Loading WASM module...');
            
            if (!window.wasmVideoProcessor) {
                throw new Error('WASM video processor not available');
            }
            
            const initialized = await window.wasmVideoProcessor.initialize();
            if (!initialized) {
                throw new Error('Failed to initialize WASM processor');
            }
            
            this.wasmModule = window.wasmVideoProcessor;
            console.log('WASM module loaded successfully');
        } catch (error) {
            throw new Error('Failed to load WASM module: ' + error.message);
        }
    }
    
    async fileToArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = () => reject(reader.error);
            reader.readAsArrayBuffer(file);
        });
    }
    
    displayMedia(file, fileType) {
        const url = URL.createObjectURL(file);
        
        // Clear previous content
        this.originalContainer.innerHTML = '';
        this.processedContainer.innerHTML = `
            <div class="placeholder">
                <i class="fas fa-magic"></i>
                <p>Apply operations to see results</p>
            </div>
        `;
        
        if (fileType === 'image') {
            const img = document.createElement('img');
            img.src = url;
            img.alt = 'Original image';
            this.originalContainer.appendChild(img);
        } else if (fileType === 'video') {
            const video = document.createElement('video');
            video.src = url;
            video.controls = true;
            video.autoplay = false;
            video.loop = true;
            this.originalContainer.appendChild(video);
        }
        
        this.mediaTitle.textContent = file.name;
        this.previewSection.style.display = 'block';
    }
    
    showControls(fileType) {
        this.controlsTitle.textContent = `${fileType === 'image' ? 'Image' : 'Video'} Processing Controls`;
        this.mediaTypeBadge.textContent = fileType;
        this.mediaTypeBadge.className = `media-type-badge ${fileType}`;
        
        // Show processing mode badge
        if (this.useWASM) {
            this.processingModeBadge.textContent = 'WebAssembly';
            this.processingModeBadge.className = 'processing-mode-badge wasm';
            this.processingModeBadge.style.display = 'inline-block';
        } else {
            this.processingModeBadge.textContent = 'Server-side';
            this.processingModeBadge.className = 'processing-mode-badge server';
            this.processingModeBadge.style.display = 'inline-block';
        }
        
        this.controlsSection.style.display = 'block';
    }
    
    async loadOperations() {
        if (!this.currentFileType) return;
        
        try {
            const endpoint = this.currentFileType === 'image' ? '/get_image_operations' : '/get_video_operations';
            const response = await fetch(endpoint);
            const operations = await response.json();
            
            this.availableOperations = operations;
            this.populateOperationSelect();
            this.displayAvailableOperations();
        } catch (error) {
            console.error('Failed to load operations:', error);
        }
    }
    
    populateOperationSelect() {
        this.operationSelect.innerHTML = '<option value="">Choose an operation...</option>';
        
        this.availableOperations.forEach(op => {
            const option = document.createElement('option');
            option.value = op.name;
            option.textContent = op.display_name;
            this.operationSelect.appendChild(option);
        });
    }
    
    displayAvailableOperations() {
        this.operationsList.innerHTML = '';
        
        this.availableOperations.forEach(op => {
            const card = document.createElement('div');
            card.className = 'operation-card';
            card.innerHTML = `
                <h5>${op.display_name}</h5>
                <p>${op.description}</p>
            `;
            card.addEventListener('click', () => {
                this.operationSelect.value = op.name;
                this.updateOperationInfo();
                this.showOperationModal();
            });
            this.operationsList.appendChild(card);
        });
    }
    
    showOperationModal() {
        this.operationModal.style.display = 'flex';
        this.updateOperationInfo();
    }
    
    hideOperationModal() {
        this.operationModal.style.display = 'none';
        this.operationSelect.value = '';
        this.operationParams.innerHTML = '';
        this.modalAdd.disabled = true;
    }
    
    updateOperationInfo() {
        const selectedName = this.operationSelect.value;
        
        if (!selectedName) {
            this.operationDescription.innerHTML = '<p>Select an operation to see its description and parameters.</p>';
            this.operationParams.innerHTML = '';
            this.modalAdd.disabled = true;
            return;
        }
        
        const operation = this.availableOperations.find(op => op.name === selectedName);
        if (!operation) return;
        
        // Update description
        this.operationDescription.innerHTML = `
            <div class="operation-info-header">
                <i class="fas fa-magic"></i>
                <h4>${operation.display_name}</h4>
            </div>
            <p>${operation.description}</p>
        `;
        
        // Update parameters
        this.operationParams.innerHTML = '';
        
        if (operation.params && operation.params.length > 0) {
            const paramsContainer = document.createElement('div');
            paramsContainer.className = 'params-container';
            
            operation.params.forEach(param => {
                const paramGroup = document.createElement('div');
                paramGroup.className = 'param-group';
                
                const labelContainer = document.createElement('div');
                labelContainer.className = 'param-label-container';
                
                const label = document.createElement('label');
                label.textContent = this.formatParameterName(param.name);
                labelContainer.appendChild(label);
                
                if (param.description) {
                    const tooltip = document.createElement('span');
                    tooltip.className = 'param-tooltip';
                    tooltip.innerHTML = `<i class="fas fa-info-circle"></i>`;
                    tooltip.title = param.description;
                    labelContainer.appendChild(tooltip);
                }
                
                paramGroup.appendChild(labelContainer);
                
                if (param.options) {
                    // Dropdown for options
                    const select = document.createElement('select');
                    select.name = param.name;
                    select.className = 'param-select';
                    
                    param.options.forEach(option => {
                        const opt = document.createElement('option');
                        opt.value = option.value;
                        opt.textContent = option.label;
                        if (option.value === param.default) opt.selected = true;
                        select.appendChild(opt);
                    });
                    
                    paramGroup.appendChild(select);
                } else if (param.type === 'float' || param.type === 'int') {
                    // Enhanced slider with better styling
                    const sliderContainer = document.createElement('div');
                    sliderContainer.className = 'slider-container';
                    
                    const sliderTrack = document.createElement('div');
                    sliderTrack.className = 'slider-track';
                    
                    const range = document.createElement('input');
                    range.type = 'range';
                    range.name = param.name;
                    range.className = 'param-slider';
                    range.min = param.min || 0;
                    range.max = param.max || 100;
                    range.step = param.step || (param.type === 'float' ? 0.1 : 1);
                    range.value = param.default;
                    
                    const valueContainer = document.createElement('div');
                    valueContainer.className = 'value-container';
                    
                    const valueDisplay = document.createElement('input');
                    valueDisplay.type = 'number';
                    valueDisplay.className = 'param-value';
                    valueDisplay.min = range.min;
                    valueDisplay.max = range.max;
                    valueDisplay.step = range.step;
                    valueDisplay.value = param.default;
                    
                    const rangeInfo = document.createElement('div');
                    rangeInfo.className = 'range-info';
                    rangeInfo.innerHTML = `<span class="range-min">${param.min || 0}</span><span class="range-max">${param.max || 100}</span>`;
                    
                    // Sync range and number inputs with enhanced feedback
                    const updateValue = () => {
                        const percentage = ((range.value - range.min) / (range.max - range.min)) * 100;
                        range.style.setProperty('--slider-progress', percentage + '%');
                    };
                    
                    range.addEventListener('input', () => {
                        valueDisplay.value = range.value;
                        updateValue();
                    });
                    
                    valueDisplay.addEventListener('input', () => {
                        const value = Math.max(range.min, Math.min(range.max, valueDisplay.value));
                        range.value = value;
                        valueDisplay.value = value;
                        updateValue();
                    });
                    
                    // Initialize slider progress
                    updateValue();
                    
                    sliderTrack.appendChild(range);
                    sliderContainer.appendChild(sliderTrack);
                    valueContainer.appendChild(valueDisplay);
                    sliderContainer.appendChild(valueContainer);
                    sliderContainer.appendChild(rangeInfo);
                    paramGroup.appendChild(sliderContainer);
                }
                
                paramsContainer.appendChild(paramGroup);
            });
            
            this.operationParams.appendChild(paramsContainer);
        } else {
            const noParamsMessage = document.createElement('div');
            noParamsMessage.className = 'no-params-message';
            noParamsMessage.innerHTML = '<i class="fas fa-check-circle"></i> This operation requires no additional parameters';
            this.operationParams.appendChild(noParamsMessage);
        }
        
        this.modalAdd.disabled = false;
    }
    
    formatParameterName(name) {
        return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    addOperation() {
        const selectedName = this.operationSelect.value;
        const operation = this.availableOperations.find(op => op.name === selectedName);
        
        if (!operation) return;
        
        // Collect parameter values
        const params = {};
        const paramInputs = this.operationParams.querySelectorAll('input, select');
        
        paramInputs.forEach(input => {
            if (input.name) {
                const value = input.type === 'number' || input.type === 'range' 
                    ? parseFloat(input.value) 
                    : input.value;
                params[input.name] = value;
            }
        });
        
        // Add to applied operations
        const appliedOp = {
            name: operation.name,
            display_name: operation.display_name,
            params: params,
            id: Date.now() // Simple ID generation
        };
        
        this.appliedOperations.push(appliedOp);
        this.updateAppliedOperations();
        this.updateProcessButton();
        this.hideOperationModal();
    }
    
    updateAppliedOperations() {
        this.operationCount.textContent = `(${this.appliedOperations.length})`;
        
        if (this.appliedOperations.length === 0) {
            this.appliedList.innerHTML = '<div class="no-operations">No operations applied yet</div>';
            return;
        }
        
        // Add pipeline info
        let pipelineInfo = '';
        if (this.appliedOperations.length > 0) {
            pipelineInfo = `
                <div class="pipeline-info">
                    <p><i class="fas fa-info-circle"></i> Operations will be applied in the order shown below. Use the arrow buttons to reorder.</p>
                </div>
            `;
        }
        
        this.appliedList.innerHTML = pipelineInfo;
        
        this.appliedOperations.forEach((op, index) => {
            const opElement = document.createElement('div');
            opElement.className = 'applied-operation';
            
            const paramsText = Object.keys(op.params).length > 0 
                ? Object.entries(op.params).map(([key, value]) => `${key}: ${value}`).join(', ')
                : 'No parameters';
            
            opElement.innerHTML = `
                <div style="display: flex; align-items: center; flex: 1;">
                    <div class="operation-order">${index + 1}</div>
                    <div class="operation-info">
                        <h6>${op.display_name}</h6>
                        <div class="operation-params-display">${paramsText}</div>
                    </div>
                </div>
                <div class="operation-actions">
                    <button class="move-btn" onclick="mediaProcessor.moveOperation(${index}, 'up')" ${index === 0 ? 'disabled' : ''}>
                        <i class="fas fa-arrow-up"></i>
                    </button>
                    <button class="move-btn" onclick="mediaProcessor.moveOperation(${index}, 'down')" ${index === this.appliedOperations.length - 1 ? 'disabled' : ''}>
                        <i class="fas fa-arrow-down"></i>
                    </button>
                    <button class="remove-operation" onclick="mediaProcessor.removeOperation(${index})">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;
            
            this.appliedList.appendChild(opElement);
        });
    }
    
    removeOperation(index) {
        this.appliedOperations.splice(index, 1);
        this.updateAppliedOperations();
        this.updateProcessButton();
    }
    
    moveOperation(index, direction) {
        if (direction === 'up' && index > 0) {
            // Swap with previous operation
            [this.appliedOperations[index - 1], this.appliedOperations[index]] = 
            [this.appliedOperations[index], this.appliedOperations[index - 1]];
        } else if (direction === 'down' && index < this.appliedOperations.length - 1) {
            // Swap with next operation
            [this.appliedOperations[index], this.appliedOperations[index + 1]] = 
            [this.appliedOperations[index + 1], this.appliedOperations[index]];
        }
        
        this.updateAppliedOperations();
    }
    
    updateProcessButton() {
        this.processBtn.disabled = this.appliedOperations.length === 0;
        this.downloadBtn.style.display = 'none';
    }
    
    async processMedia() {
        if (!this.currentFile || this.appliedOperations.length === 0) return;
        
        this.showProcessingOverlay();
        
        try {
            if (this.useWASM) {
                // Process using WASM
                await this.processWithWASM();
            } else {
                // Process using server-side
                await this.processWithServer();
            }
        } catch (error) {
            this.showError('Processing failed: ' + error.message);
        } finally {
            this.hideProcessingOverlay();
        }
    }
    
    async processWithServer() {
        const endpoint = this.currentFileType === 'image' ? '/process_image' : '/process_video';
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                file_id: this.currentFile.file_id,
                operations: this.appliedOperations.map(op => ({
                    name: op.name,
                    params: op.params
                }))
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Clear any existing processed media first
            this.processedContainer.innerHTML = '<div class="placeholder"><i class="fas fa-hourglass-half"></i><p>Loading processed media...</p></div>';
            
            // Display the new processed media
            setTimeout(() => {
                this.displayProcessedMedia(result.processed_file);
            }, 100);
            
            this.downloadBtn.style.display = 'inline-flex';
            this.downloadBtn.setAttribute('data-filename', result.processed_file);
            this.showSuccess(`Processing completed! Applied ${result.operations_applied} operations.`);
        } else {
            this.showError(result.error || 'Processing failed');
        }
    }
    
    async processWithWASM() {
        if (!this.wasmModule || !this.videoBuffer) {
            throw new Error('WASM module or video buffer not available');
        }
        
        try {
            console.log('Processing with WASM...', this.appliedOperations);
            
            // Convert the file buffer to a File object for processing
            const videoFile = new File([this.videoBuffer], this.currentFile.filename, { type: 'video/mp4' });
            
            // Process the video file with WASM
            await this.wasmModule.processVideoFile(videoFile);
            
            // Apply operations in chunks
            for (let i = 0; i < this.appliedOperations.length; i++) {
                const operation = this.appliedOperations[i];
                
                // Update processing status
                this.processingStatus.textContent = `Applying ${operation.display_name}... (${i + 1}/${this.appliedOperations.length})`;
                
                await this.applyWASMOperation(operation);
                
                // Small delay to allow UI updates and prevent blocking
                await new Promise(resolve => setTimeout(resolve, 100));
            }
            
            // Export the processed video
            this.processingStatus.textContent = 'Exporting processed video...';
            const processedData = await this.wasmModule.exportVideo();
            
            // Create blob and display
            const processedBlob = new Blob([processedData], { type: 'application/octet-stream' });
            const processedUrl = URL.createObjectURL(processedBlob);
            
            // For display, we'll create a video element with the original video
            // In a real implementation, you'd convert the processed data back to a video format
            this.displayProcessedWASMVideo(processedUrl);
            
            // Enable download
            this.downloadBtn.style.display = 'inline-flex';
            this.downloadBtn.setAttribute('data-wasm-url', processedUrl);
            this.downloadBtn.setAttribute('data-filename', 'processed_' + this.currentFile.filename);
            
            this.showSuccess(`WASM processing completed! Applied ${this.appliedOperations.length} operations.`);
            
        } catch (error) {
            console.error('WASM processing error:', error);
            throw error;
        } finally {
            // Cleanup WASM memory
            this.wasmModule.cleanup();
        }
    }
    
    displayProcessedMedia(filename) {
        // Add timestamp to prevent caching
        const timestamp = new Date().getTime();
        const url = `/download/${filename}?t=${timestamp}`;
        
        this.processedContainer.innerHTML = '';
        
        if (this.currentFileType === 'image') {
            const img = document.createElement('img');
            img.src = url;
            img.alt = 'Processed image';
            img.className = 'processed-image';
            
            // Add loading state
            img.onload = () => {
                img.classList.add('loaded');
            };
            
            this.processedContainer.appendChild(img);
        } else if (this.currentFileType === 'video') {
            const video = document.createElement('video');
            video.src = url;
            video.controls = true;
            video.autoplay = false;
            video.loop = true;
            video.className = 'processed-video';
            this.processedContainer.appendChild(video);
        }
    }
    
    async applyWASMOperation(operation) {
        const params = operation.params;
        
        switch (operation.name) {
            case 'reverse':
                await this.wasmModule.reverseVideo();
                break;
                
            case 'swap_channels':
                const channel1 = params.channel1 || 0;
                const channel2 = params.channel2 || 1;
                await this.wasmModule.swapChannels(channel1, channel2);
                break;
                
            case 'clip_channel':
                const clipChannel = params.channel || 0;
                const minVal = params.min_val || 0;
                const maxVal = params.max_val || 255;
                await this.wasmModule.clipChannel(clipChannel, minVal, maxVal);
                break;
                
            case 'scale_channel':
                const scaleChannel = params.channel || 0;
                const scaleFactor = params.scale_factor || 1.0;
                await this.wasmModule.scaleChannel(scaleChannel, scaleFactor);
                break;
                
            default:
                console.warn(`Unknown WASM operation: ${operation.name}`);
        }
    }
    
    displayProcessedWASMVideo(dataUrl) {
        this.processedContainer.innerHTML = '';
        
        // Create a placeholder video element
        // In a real implementation, you'd convert the processed data back to a proper video format
        const placeholder = document.createElement('div');
        placeholder.className = 'processed-placeholder';
        placeholder.innerHTML = `
            <div class="wasm-result">
                <i class="fas fa-microchip"></i>
                <h4>Video Processed with WebAssembly</h4>
                <p>Processing completed successfully!</p>
                <p><strong>Operations applied:</strong> ${this.appliedOperations.length}</p>
                <div class="video-info">
                    ${this.wasmModule.getVideoInfo() ? 
                        `<small>Frames: ${this.wasmModule.getVideoInfo().numFrames}, 
                         Size: ${this.wasmModule.getVideoInfo().width}x${this.wasmModule.getVideoInfo().height}</small>` 
                        : ''}
                </div>
            </div>
        `;
        
        this.processedContainer.appendChild(placeholder);
    }
    
    downloadResult() {
        const wasmUrl = this.downloadBtn.getAttribute('data-wasm-url');
        const filename = this.downloadBtn.getAttribute('data-filename');
        
        if (wasmUrl) {
            // Download WASM-processed file
            const link = document.createElement('a');
            link.href = wasmUrl;
            link.download = filename || 'processed_video.dat';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } else if (filename) {
            // Download server-processed file
            window.open(`/download/${filename}`, '_blank');
        }
    }
    
    resetApplication() {
        this.currentFile = null;
        this.currentFileType = null;
        this.appliedOperations = [];
        
        this.previewSection.style.display = 'none';
        this.controlsSection.style.display = 'none';
        this.fileInput.value = '';
        
        this.updateAppliedOperations();
        this.updateProcessButton();
    }
    
    showUploadProgress() {
        this.uploadProgress.style.display = 'block';
        this.progressFill.style.width = '0%';
        
        // Simulate progress
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress >= 100) {
                progress = 100;
                clearInterval(interval);
            }
            this.progressFill.style.width = progress + '%';
            this.progressText.textContent = `Uploading... ${Math.round(progress)}%`;
        }, 200);
    }
    
    hideUploadProgress() {
        setTimeout(() => {
            this.uploadProgress.style.display = 'none';
        }, 500);
    }
    
    showProcessingOverlay() {
        this.processingOverlay.style.display = 'flex';
        this.processingStatus.textContent = 'Initializing...';
        this.processingProgressFill.style.width = '0%';
        
        // Simulate processing progress
        let progress = 0;
        const messages = [
            'Loading media...',
            'Applying operations...',
            'Processing frames...',
            'Optimizing output...',
            'Finalizing...'
        ];
        
        const interval = setInterval(() => {
            progress += Math.random() * 10;
            if (progress >= 100) {
                progress = 100;
                this.processingStatus.textContent = 'Complete!';
                clearInterval(interval);
            } else {
                const messageIndex = Math.floor((progress / 100) * messages.length);
                this.processingStatus.textContent = messages[messageIndex] || 'Processing...';
            }
            this.processingProgressFill.style.width = progress + '%';
        }, 300);
    }
    
    hideProcessingOverlay() {
        setTimeout(() => {
            this.processingOverlay.style.display = 'none';
        }, 1000);
    }
    
    showSuccess(message) {
        this.showMessage(message, 'success');
    }
    
    showError(message) {
        this.showMessage(message, 'error');
    }
    
    showMessage(message, type) {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.success-message, .error-message');
        existingMessages.forEach(msg => msg.remove());
        
        // Create new message
        const messageElement = document.createElement('div');
        messageElement.className = `${type}-message`;
        messageElement.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        `;
        
        // Insert after header
        const header = document.querySelector('.header');
        header.insertAdjacentElement('afterend', messageElement);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            messageElement.remove();
        }, 5000);
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.mediaProcessor = new MediaProcessor();
});