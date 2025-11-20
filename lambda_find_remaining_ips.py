import boto3
import ipaddress

ec2 = boto3.client('ec2')

# 이 값보다 작은 서브넷(총 호스트 수)만 free IP 전체 리스트를 리턴
MAX_HOSTS_FOR_FULL_LIST = 512


def list_subnets(vpc_id=None):
    """계정/리전의 모든 subnet 목록 가져오기 (옵션: vpc_id로 필터)"""
    params = {}
    if vpc_id:
        params["Filters"] = [{"Name": "vpc-id", "Values": [vpc_id]}]

    subnets = []
    while True:
        resp = ec2.describe_subnets(**params)
        subnets.extend(resp["Subnets"])
        token = resp.get("NextToken")
        if not token:
            break
        params["NextToken"] = token
    return subnets


def get_used_ips_by_subnet(subnet_id):
    """특정 subnet에서 사용 중인 private IP 목록 조회"""
    used_ips = set()
    params = {
        "Filters": [
            {"Name": "subnet-id", "Values": [subnet_id]}
        ]
    }
    while True:
        resp = ec2.describe_network_interfaces(**params)
        for eni in resp.get("NetworkInterfaces", []):
            for ipitem in eni.get("PrivateIpAddresses", []):
                used_ips.add(ipitem["PrivateIpAddress"])

        token = resp.get("NextToken")
        if not token:
            break
        params["NextToken"] = token

    return used_ips


def calc_free_ips(cidr, used_ips):
    """CIDR와 사용 중 IP를 기반으로 남은 IP 계산"""
    net = ipaddress.ip_network(cidr)
    hosts = list(net.hosts())
    total_hosts = len(hosts)

    if total_hosts <= MAX_HOSTS_FOR_FULL_LIST:
        free_ips = [str(ip) for ip in hosts if str(ip) not in used_ips]
        return {
            "total_ips": total_hosts,
            "used_ips_count": len(used_ips),
            "free_ips_count": len(free_ips),
            "free_ips": free_ips,  # 전체 리스트
        }
    else:
        # 큰 서브넷은 개수만 계산 (메모리/시간 보호)
        free_count = 0
        for ip in hosts:
            if str(ip) not in used_ips:
                free_count += 1
        return {
            "total_ips": total_hosts,
            "used_ips_count": len(used_ips),
            "free_ips_count": free_count,
            "free_ips": None,      # 너무 커서 리스트는 생략
        }


def lambda_handler(event, context):
    """
    event 예시:
    {
      "vpc_id": "vpc-0abc1234def567890"   # 옵션, 없으면 전체 VPC
    }
    """
    vpc_id = event.get("vpc_id")  # 없으면 전체 subnet

    subnets = list_subnets(vpc_id=vpc_id)

    results = []

    for subnet in subnets:
        subnet_id = subnet["SubnetId"]
        cidr = subnet["CidrBlock"]

        used_ips = get_used_ips_by_subnet(subnet_id)
        stat = calc_free_ips(cidr, used_ips)

        result = {
            "subnet_id": subnet_id,
            "cidr": cidr,
            "availability_zone": subnet.get("AvailabilityZone"),
            "total_ips": stat["total_ips"],
            "used_ips_count": stat["used_ips_count"],
            "free_ips_count": stat["free_ips_count"],
            # 작은 서브넷이면 free_ips에 전체 리스트, 크면 None
            "free_ips": stat["free_ips"],
        }
        results.append(result)

    return {
        "vpc_id": vpc_id,
        "subnet_count": len(results),
        "subnets": results,
    }
