// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title CarbonCreditMarket
 * @dev A standard ERC20 token for Carbon Credits (RCC) with a built-in 
 * marketplace and retirement (burning) capability for sustainability standards.
 */
contract CarbonCreditMarket is ERC20, Ownable {
    uint256 public constant PLATFORM_FEE = 2; // 2% Sustainability Fee

    // Events allow your Django backend to track transactions easily
    event CreditsMinted(address indexed farmer, uint256 amount);
    event CreditsPurchased(address indexed buyer, address indexed farmer, uint256 amount, uint256 price);
    event CreditsRetired(address indexed user, uint256 amount, string reason);

    constructor() ERC20("Regional Carbon Credit", "RCC") Ownable(msg.sender) {}

    /**
     * @dev Django backend calls this after AI verification (Dhiptanshu/Khush logic).
     * The platform pays the gas, enabling "Zero-Coin Onboarding" for farmers.
     */
    function mintVerifiedCredit(address farmer, uint256 amount) public onlyOwner {
        _mint(farmer, amount);
        emit CreditsMinted(farmer, amount);
    }

    /**
     * @dev Industrialist buys credits directly from a farmer.
     * Splits payment: 98% to Farmer, 2% to Platform Treasury.
     */
    function buyCredits(address farmer, uint256 amount) public payable {
        require(balanceOf(farmer) >= amount, "Farmer does not have enough credits");
        require(msg.value > 0, "Payment must be greater than 0");

        uint256 fee = (msg.value * PLATFORM_FEE) / 100;
        uint256 farmerAmount = msg.value - fee;

        // Transfers funds
        payable(owner()).transfer(fee); 
        payable(farmer).transfer(farmerAmount); 
        
        // Transfers the RCC tokens
        _transfer(farmer, msg.sender, amount);

        emit CreditsPurchased(msg.sender, farmer, amount, msg.value);
    }

    /**
     * @dev Professional Retirement: Industrialists call this to "use" their credits.
     * This removes the tokens from circulation to prevent double-counting.
     */
    function retireCredits(uint256 amount, string memory reason) public {
        require(balanceOf(msg.sender) >= amount, "Insufficient balance to retire credits");
        
        // _burn is an internal ERC20 function that permanently destroys tokens
        _burn(msg.sender, amount);

        emit CreditsRetired(msg.sender, amount, reason);
    }
}