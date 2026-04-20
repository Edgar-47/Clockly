import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';
import '../models/employee/employee_model.dart';

class EmployeeRemoteDatasource {
  const EmployeeRemoteDatasource(this._client);

  final ApiClient _client;

  Future<List<EmployeeModel>> getEmployees({
    String? businessId,
    bool? isActive,
    String? search,
    int page = 1,
  }) async {
    final params = <String, String>{
      'page': page.toString(),
      if (businessId != null) 'business_id': businessId,
      if (isActive != null) 'is_active': isActive.toString(),
      if (search != null && search.isNotEmpty) 'search': search,
    };
    final data = await _client.get(ApiConstants.employees, queryParams: params);
    final list = data is List ? data : (data as Map<String, dynamic>)['results'] as List? ?? [];
    return list.map((e) => EmployeeModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<EmployeeModel> getEmployee(int id) async {
    final data = await _client.get('${ApiConstants.employees}$id/') as Map<String, dynamic>;
    return EmployeeModel.fromJson(data);
  }

  Future<EmployeeModel> createEmployee(Map<String, dynamic> body) async {
    final data = await _client.post(ApiConstants.employees, body: body) as Map<String, dynamic>;
    return EmployeeModel.fromJson(data);
  }

  Future<EmployeeModel> updateEmployee(int id, Map<String, dynamic> body) async {
    final data = await _client.patch('${ApiConstants.employees}$id/', body: body)
        as Map<String, dynamic>;
    return EmployeeModel.fromJson(data);
  }

  Future<void> deactivateEmployee(int id) async {
    await _client.patch('${ApiConstants.employees}$id/', body: {'is_active': false});
  }
}
