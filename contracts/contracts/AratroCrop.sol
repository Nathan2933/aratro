// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title AratroCrop
 * @dev Smart contract for tracking agricultural stock transactions in the Aratro app
 */
contract AratroCrop {
    // Enum for stock status
    enum StockStatus { Pending, Stored, Rejected, Transferred }
    
    // Struct for Stock
    struct Stock {
        uint256 id;
        string cropType;
        uint256 quantity; // in kg (converted from tons)
        uint256 requestedQuantity; // Original requested quantity
        StockStatus status;
        address farmer;
        address warehouse;
        uint256 timestamp;
        uint256 updatedAt;
    }
    
    // Struct for StockRequest
    struct StockRequest {
        uint256 id;
        address from; // Farmer's address
        address to;   // Warehouse's address
        uint256 stockId;
        uint256 requestDate;
        StockStatus status;
        uint256 createdAt;
        uint256 updatedAt;
    }
    
    // Struct for WarehouseRequest
    struct WarehouseRequest {
        uint256 id;
        address warehouse;
        string stockType;
        uint256 quantity;
        uint256 pricePerTon;
        string description;
        string status; // "open", "closed", etc.
        uint256 datePosted;
        uint256 expiryDate;
    }
    
    // Struct for RationStockRequest
    struct RationStockRequest {
        uint256 id;
        address rationShop;
        address warehouse;
        string stockType;
        uint256 quantity;
        StockStatus status;
        uint256 requestDate;
        uint256 processedDate;
        string notes;
        string adminNotes;
        uint256 createdAt;
        uint256 updatedAt;
    }
    
    // Mapping from stock ID to Stock
    mapping(uint256 => Stock) public stocks;
    
    // Mapping from request ID to StockRequest
    mapping(uint256 => StockRequest) public stockRequests;
    
    // Mapping from request ID to WarehouseRequest
    mapping(uint256 => WarehouseRequest) public warehouseRequests;
    
    // Mapping from request ID to RationStockRequest
    mapping(uint256 => RationStockRequest) public rationStockRequests;
    
    // Counter for stock IDs
    uint256 private stockIdCounter;
    
    // Counter for stock request IDs
    uint256 private stockRequestIdCounter;
    
    // Counter for warehouse request IDs
    uint256 private warehouseRequestIdCounter;
    
    // Counter for ration stock request IDs
    uint256 private rationStockRequestIdCounter;
    
    // Events
    event StockCreated(uint256 indexed id, string cropType, uint256 quantity, address indexed farmer, address indexed warehouse);
    event StockStatusUpdated(uint256 indexed id, StockStatus status);
    event StockRequestCreated(uint256 indexed id, address indexed from, address indexed to, uint256 stockId);
    event StockRequestStatusUpdated(uint256 indexed id, StockStatus status);
    event WarehouseRequestCreated(uint256 indexed id, address indexed warehouse, string stockType, uint256 quantity);
    event RationStockRequestCreated(uint256 indexed id, address indexed rationShop, address indexed warehouse, string stockType);
    event RationStockRequestStatusUpdated(uint256 indexed id, StockStatus status);
    
    /**
     * @dev Create a new stock entry
     * @param _cropType Type of crop
     * @param _quantity Quantity in kg
     * @param _requestedQuantity Original requested quantity
     * @param _farmer Farmer's address
     * @param _warehouse Warehouse's address
     * @return ID of the created stock
     */
    function createStock(
        string memory _cropType,
        uint256 _quantity,
        uint256 _requestedQuantity,
        address _farmer,
        address _warehouse
    ) public returns (uint256) {
        stockIdCounter++;
        uint256 stockId = stockIdCounter;
        
        stocks[stockId] = Stock({
            id: stockId,
            cropType: _cropType,
            quantity: _quantity,
            requestedQuantity: _requestedQuantity,
            status: StockStatus.Pending,
            farmer: _farmer,
            warehouse: _warehouse,
            timestamp: block.timestamp,
            updatedAt: block.timestamp
        });
        
        emit StockCreated(stockId, _cropType, _quantity, _farmer, _warehouse);
        
        return stockId;
    }
    
    /**
     * @dev Update the status of a stock
     * @param _stockId ID of the stock
     * @param _status New status
     */
    function updateStockStatus(uint256 _stockId, StockStatus _status) public {
        require(_stockId <= stockIdCounter, "Stock does not exist");
        
        Stock storage stock = stocks[_stockId];
        stock.status = _status;
        stock.updatedAt = block.timestamp;
        
        emit StockStatusUpdated(_stockId, _status);
    }
    
    /**
     * @dev Create a new stock request
     * @param _from Farmer's address
     * @param _to Warehouse's address
     * @param _stockId ID of the stock
     * @return ID of the created request
     */
    function createStockRequest(
        address _from,
        address _to,
        uint256 _stockId
    ) public returns (uint256) {
        require(_stockId <= stockIdCounter, "Stock does not exist");
        
        stockRequestIdCounter++;
        uint256 requestId = stockRequestIdCounter;
        
        stockRequests[requestId] = StockRequest({
            id: requestId,
            from: _from,
            to: _to,
            stockId: _stockId,
            requestDate: block.timestamp,
            status: StockStatus.Pending,
            createdAt: block.timestamp,
            updatedAt: block.timestamp
        });
        
        emit StockRequestCreated(requestId, _from, _to, _stockId);
        
        return requestId;
    }
    
    /**
     * @dev Update the status of a stock request
     * @param _requestId ID of the request
     * @param _status New status
     */
    function updateStockRequestStatus(uint256 _requestId, StockStatus _status) public {
        require(_requestId <= stockRequestIdCounter, "Stock request does not exist");
        
        StockRequest storage request = stockRequests[_requestId];
        request.status = _status;
        request.updatedAt = block.timestamp;
        
        emit StockRequestStatusUpdated(_requestId, _status);
        
        // Also update the associated stock status
        updateStockStatus(request.stockId, _status);
    }
    
    /**
     * @dev Create a new warehouse request
     * @param _warehouse Warehouse's address
     * @param _stockType Type of stock
     * @param _quantity Quantity in kg
     * @param _pricePerTon Price per ton
     * @param _description Description
     * @param _expiryDate Expiry date (timestamp)
     * @return ID of the created request
     */
    function createWarehouseRequest(
        address _warehouse,
        string memory _stockType,
        uint256 _quantity,
        uint256 _pricePerTon,
        string memory _description,
        uint256 _expiryDate
    ) public returns (uint256) {
        warehouseRequestIdCounter++;
        uint256 requestId = warehouseRequestIdCounter;
        
        warehouseRequests[requestId] = WarehouseRequest({
            id: requestId,
            warehouse: _warehouse,
            stockType: _stockType,
            quantity: _quantity,
            pricePerTon: _pricePerTon,
            description: _description,
            status: "open",
            datePosted: block.timestamp,
            expiryDate: _expiryDate
        });
        
        emit WarehouseRequestCreated(requestId, _warehouse, _stockType, _quantity);
        
        return requestId;
    }
    
    /**
     * @dev Create a new ration stock request
     * @param _rationShop Ration shop's address
     * @param _warehouse Warehouse's address
     * @param _stockType Type of stock
     * @param _quantity Quantity in kg
     * @param _notes Notes
     * @return ID of the created request
     */
    function createRationStockRequest(
        address _rationShop,
        address _warehouse,
        string memory _stockType,
        uint256 _quantity,
        string memory _notes
    ) public returns (uint256) {
        rationStockRequestIdCounter++;
        uint256 requestId = rationStockRequestIdCounter;
        
        rationStockRequests[requestId] = RationStockRequest({
            id: requestId,
            rationShop: _rationShop,
            warehouse: _warehouse,
            stockType: _stockType,
            quantity: _quantity,
            status: StockStatus.Pending,
            requestDate: block.timestamp,
            processedDate: 0,
            notes: _notes,
            adminNotes: "",
            createdAt: block.timestamp,
            updatedAt: block.timestamp
        });
        
        emit RationStockRequestCreated(requestId, _rationShop, _warehouse, _stockType);
        
        return requestId;
    }
    
    /**
     * @dev Update the status of a ration stock request
     * @param _requestId ID of the request
     * @param _status New status
     * @param _adminNotes Admin notes
     */
    function updateRationStockRequestStatus(
        uint256 _requestId,
        StockStatus _status,
        string memory _adminNotes
    ) public {
        require(_requestId <= rationStockRequestIdCounter, "Ration stock request does not exist");
        
        RationStockRequest storage request = rationStockRequests[_requestId];
        request.status = _status;
        request.adminNotes = _adminNotes;
        request.processedDate = block.timestamp;
        request.updatedAt = block.timestamp;
        
        emit RationStockRequestStatusUpdated(_requestId, _status);
    }
    
    /**
    * @dev Get stock details
    * @param _stockId ID of the stock
    * @return id Stock ID
    * @return cropType Type of crop
    * @return quantity Quantity in kg
    * @return requestedQuantity Original requested quantity
    * @return status Status of the stock
    * @return farmer Farmer's address
    * @return warehouse Warehouse's address
    * @return timestamp Creation timestamp
    * @return updatedAt Last update timestamp
    */
    function getStock(uint256 _stockId) public view returns (
        uint256 id,
        string memory cropType,
        uint256 quantity,
        uint256 requestedQuantity,
        StockStatus status,
        address farmer,
        address warehouse,
        uint256 timestamp,
        uint256 updatedAt
    ) {
        require(_stockId <= stockIdCounter, "Stock does not exist");
        
        Stock storage stock = stocks[_stockId];
        
        return (
            stock.id,
            stock.cropType,
            stock.quantity,
            stock.requestedQuantity,
            stock.status,
            stock.farmer,
            stock.warehouse,
            stock.timestamp,
            stock.updatedAt
        );
    }
    
    /**
    * @dev Get stock request details
    * @param _requestId ID of the request
    * @return id Request ID
    * @return from Farmer's address
    * @return to Warehouse's address
    * @return stockId ID of the stock
    * @return requestDate Request date
    * @return status Status of the request
    * @return createdAt Creation timestamp
    * @return updatedAt Last update timestamp
    */
    function getStockRequest(uint256 _requestId) public view returns (
        uint256 id,
        address from,
        address to,
        uint256 stockId,
        uint256 requestDate,
        StockStatus status,
        uint256 createdAt,
        uint256 updatedAt
    ) {
        require(_requestId <= stockRequestIdCounter, "Stock request does not exist");
        
        StockRequest storage request = stockRequests[_requestId];
        
        return (
            request.id,
            request.from,
            request.to,
            request.stockId,
            request.requestDate,
            request.status,
            request.createdAt,
            request.updatedAt
        );
    }
    
    /**
     * @dev Get the total number of stocks
     * @return Total number of stocks
     */
    function getTotalStocks() public view returns (uint256) {
        return stockIdCounter;
    }
    
    /**
     * @dev Get the total number of stock requests
     * @return Total number of stock requests
     */
    function getTotalStockRequests() public view returns (uint256) {
        return stockRequestIdCounter;
    }
    
    /**
     * @dev Get the total number of warehouse requests
     * @return Total number of warehouse requests
     */
    function getTotalWarehouseRequests() public view returns (uint256) {
        return warehouseRequestIdCounter;
    }
    
    /**
     * @dev Get the total number of ration stock requests
     * @return Total number of ration stock requests
     */
    function getTotalRationStockRequests() public view returns (uint256) {
        return rationStockRequestIdCounter;
    }
} 