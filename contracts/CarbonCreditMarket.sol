// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title CarbonCreditMarket
 * @dev Standard ERC20 for Regional Carbon Credits (RCC)
 */
contract CarbonCreditMarket is ERC20, Ownable {
    uint256 public constant PLATFORM_FEE = 2; // 2% Fee

    event CreditsMinted(address indexed farmer, uint256 amount);
    event CreditsPurchased(address indexed buyer, address indexed farmer, uint256 amount, uint256 price);
    event CreditsRetired(address indexed user, uint256 amount, string reason);

    constructor() ERC20("Regional Carbon Credit", "RCC") Ownable(msg.sender) {}

    function mintVerifiedCredit(address farmer, uint256 amount) public onlyOwner {
        _mint(farmer, amount);
        emit CreditsMinted(farmer, amount);
    }

    function buyCredits(address farmer, uint256 amount) public payable {
        require(balanceOf(farmer) >= amount, "Insufficient credits");
        require(msg.value > 0, "Payment must be > 0");

        uint256 fee = (msg.value * PLATFORM_FEE) / 100;
        uint256 farmerAmount = msg.value - fee;

        payable(owner()).transfer(fee); 
        payable(farmer).transfer(farmerAmount);
        
        _transfer(farmer, msg.sender, amount);
        emit CreditsPurchased(msg.sender, farmer, amount, msg.value);
    }

    function retireCredits(uint256 amount, string memory reason) public {
        require(balanceOf(msg.sender) >= amount, "Insufficient balance");
        _burn(msg.sender, amount);
        emit CreditsRetired(msg.sender, amount, reason);
    }
}