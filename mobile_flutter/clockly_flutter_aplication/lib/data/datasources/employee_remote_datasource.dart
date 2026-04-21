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
      if (isActive != null) 'is_active': isActive.toString(),
      if (search != null && search.isNotEmpty) 'search': search,
    };
    final data = await _client.get(ApiConstants.employees, queryParams: params);
    // Backend returns {"items": [...]}
    final list = data is List ? data : (data as Map<String, dynamic>)['items'] as List? ?? [];
    return list.map((e) => EmployeeModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<EmployeeModel> getEmployee(int id) async {
    final data = await _client.get('${ApiConstants.employees}/$id') as Map<String, dynamic>;
    // Backend returns {"employee": {...}}
    final employee = data['employee'] as Map<String, dynamic>? ?? data;
    return EmployeeModel.fromJson(employee);
  }

  Future<EmployeeModel> createEmployee(Map<String, dynamic> body) async {
    final data = await _client.post(ApiConstants.employees, body: body) as Map<String, dynamic>;
    // Backend returns {"employee": {...}}
    final employee = data['employee'] as Map<String, dynamic>? ?? data;
    return EmployeeModel.fromJson(employee);
  }

  Future<EmployeeModel> updateEmployee(int id, Map<String, dynamic> body) async {
    // Backend uses PUT (not PATCH) for full employee update
    final data = await _client.put('${ApiConstants.employees}/$id', body: body)
        as Map<String, dynamic>;
    // Backend returns {"employee": {...}}
    final employee = data['employee'] as Map<String, dynamic>? ?? data;
    return EmployeeModel.fromJson(employee);
  }

  Future<void> deactivateEmployee(int id) async {
    // Backend PATCH /{id} for partial updates (toggle active)
    await _client.patch('${ApiConstants.employees}/$id', body: {'active': false});
  }
}
