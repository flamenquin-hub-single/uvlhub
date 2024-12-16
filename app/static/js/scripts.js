    function downloadDataset(datasetId, format) {
        const url = `/dataset/download/${datasetId}/${format}`;
        window.location.href = url;
    }
        
        