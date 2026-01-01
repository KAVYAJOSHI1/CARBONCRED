const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with the account:", deployer.address);

  const Market = await hre.ethers.getContractFactory("CarbonCreditMarket");
  const market = await Market.deploy();

  await market.waitForDeployment();

  console.log("CarbonCreditMarket deployed to:", await market.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});