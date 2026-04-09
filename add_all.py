import subprocess

stores = [
    "30001-BROOKEFIELDS-MALL-COIMBATORE",
    "Spar-50005-Spectrum-Mall-Noida",
    "20003_spar_mantri_mall",
    "Spar-20016-TSM-Mall-Udupi",
    "SPAR-20009-FORUM-MALL-MANGALORE",
    "Spar-30003-FVM-Chennai",
    "Spar-30006-VRMAllchennai",
    "Spar-30008-Langval-mall-Thanjavur",
    "Spar-20015-PSN-Mall-Bangalore",
    "Spar-10004-Forum-Mall-Hyderabad",
    "Spar-30005-Prozone-Mall-Coimbatore",
    "Spar-20005-City-Center-Mall-Mangalore",
    "10008_Sarath_Hyderabad",
    "Spar-20007OMR",
    "Spar-60003-Vegas-Mall-Delhi",
    "SPAR-30007-Marina-Mall-Chennai"
]

conversions = {
    "30001-BROOKEFIELDS-MALL-COIMBATORE": "Spar-30001-Brookefields-Mall-Coimbatore",
    "Spar-50005-Spectrum-Mall-Noida": "Spar-50005-Spectrum-Mall-Noida",
    "20003_spar_mantri_mall": "Spar-20003-Mantri-Mall",
    "Spar-20016-TSM-Mall-Udupi": "Spar-20016-TSM-Mall-Udupi",
    "SPAR-20009-FORUM-MALL-MANGALORE": "Spar-20009-Forum-Mall-Mangalore",
    "Spar-30003-FVM-Chennai": "Spar-30003-FVM-Chennai",
    "Spar-30006-VRMAllchennai": "Spar-30006-VR-Mall-Chennai",
    "Spar-30008-Langval-mall-Thanjavur": "Spar-30008-Langval-Mall-Thanjavur",
    "Spar-20015-PSN-Mall-Bangalore": "Spar-20015-PSN-Mall-Bangalore",
    "Spar-10004-Forum-Mall-Hyderabad": "Spar-10004-Forum-Mall-Hyderabad",
    "Spar-30005-Prozone-Mall-Coimbatore": "Spar-30005-Prozone-Mall-Coimbatore",
    "Spar-20005-City-Center-Mall-Mangalore": "Spar-20005-City-Center-Mall-Mangalore",
    "10008_Sarath_Hyderabad": "Spar-10008-Sarath-Hyderabad",
    "Spar-20007OMR": "Spar-20007-OMR",
    "Spar-60003-Vegas-Mall-Delhi": "Spar-60003-Vegas-Mall-Delhi",
    "SPAR-30007-Marina-Mall-Chennai": "Spar-30007-Marina-Mall-Chennai",
}

for code in stores:
    display_name = conversions.get(code, code)
    print(f"\\n[{code}] -> [{display_name}]")
    cmd = ["python", "-X", "utf8", "scripts/add_store.py", "--store-code", code, "--display-name", display_name]
    try:
        subprocess.run(cmd, check=False)
    except Exception as e:
        print(f"Error for {code}: {e}")
