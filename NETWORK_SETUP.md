# Network Setup for Aratro

This guide explains how to make your Aratro application accessible to other computers on the same local network.

## Running the Application for Network Access

1. Make sure you're in the project directory:
   ```
   cd /path/to/aratro
   ```

2. Run the network script:
   ```
   ./run_network.sh
   ```

3. The script will display your local IP address and the URL that other computers can use to access the application.
   Example output:
   ```
   Your local IP address is: 192.168.1.100
   Other computers on the network can access this application at: http://192.168.1.100:8080
   ```

## Blockchain Setup for Network Access

If you're using Ganache for the blockchain, you need to configure it to be accessible from other machines:

1. **On the server machine (where Ganache is running):**
   - Open Ganache
   - Go to Settings (gear icon)
   - Under the 'SERVER' tab, change HOSTNAME from '127.0.0.1' to '0.0.0.0'
   - Click 'SAVE AND RESTART'

2. **On client machines:**
   - Set the BLOCKCHAIN_URL environment variable to point to the server's IP address:
     ```
     export BLOCKCHAIN_URL=http://192.168.1.100:7545
     ```
   - Replace 192.168.1.100 with the actual IP address of the server machine

3. **Testing the blockchain connection:**
   - Use the provided test script to check if the blockchain is accessible:
     ```
     # Test the default or environment-specified blockchain URL
     ./test_blockchain_connection.py
     
     # Or specify a blockchain URL directly
     ./test_blockchain_connection.py http://192.168.1.100:7545
     ```
   - The script will perform both HTTP and Web3 connection tests and provide detailed output

4. **Alternative manual test:**
   - You can also test if the blockchain is accessible by using a web browser on the client machine
   - Navigate to http://192.168.1.100:7545 (replace with the actual server IP)
   - If you see a JSON response, the blockchain is accessible

## Accessing from Other Computers

1. On other computers in the same network, open a web browser.

2. Enter the URL displayed by the run_network.sh script (e.g., http://192.168.1.100:8080).

3. You should now be able to access the Aratro application from this computer.

## Troubleshooting

If other computers cannot access the application, check the following:

1. **Firewall Settings**: Make sure your firewall allows incoming connections on ports 8080 (for the web app) and 7545 (for Ganache).
   - On Linux: Check your firewall settings with `sudo ufw status` or `sudo firewall-cmd --list-all`
   - You may need to add rules to allow these ports:
     ```
     sudo ufw allow 8080/tcp
     sudo ufw allow 7545/tcp
     ```
   - Or with firewalld:
     ```
     sudo firewall-cmd --permanent --add-port=8080/tcp
     sudo firewall-cmd --permanent --add-port=7545/tcp
     sudo firewall-cmd --reload
     ```

2. **Network Isolation**: Ensure both computers are on the same network and subnet.

3. **Database Access**: If you're using a local database, you may need to configure it to accept connections from other machines.

4. **Test Connectivity**: Try pinging the server machine from the client machine to verify basic network connectivity.

## Security Considerations

When making your application accessible over the network:

1. This setup is intended for development or internal use only. Do not expose your application to the internet without proper security measures.

2. Consider using HTTPS for production environments.

3. Be aware that anyone on your local network can access the application when it's running with the network script.

4. The database credentials in your .env file should be kept secure. 