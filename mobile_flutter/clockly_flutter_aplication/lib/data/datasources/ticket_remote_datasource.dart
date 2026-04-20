import 'dart:io';
import 'package:http/http.dart' as http;

import '../../core/constants/api_constants.dart';
import '../../core/network/api_client.dart';
import '../models/ticket/ticket_model.dart';

class TicketRemoteDatasource {
  const TicketRemoteDatasource(this._client);

  final ApiClient _client;

  Future<List<TicketModel>> getTickets({
    String? businessId,
    String? status,
    DateTime? from,
    DateTime? to,
    int page = 1,
  }) async {
    final params = <String, String>{
      'page': page.toString(),
      if (businessId != null) 'business_id': businessId,
      if (status != null) 'status': status,
      if (from != null) 'from': from.toIso8601String().split('T').first,
      if (to != null) 'to': to.toIso8601String().split('T').first,
    };
    final data = await _client.get(ApiConstants.tickets, queryParams: params);
    final list = data is List ? data : (data as Map<String, dynamic>)['results'] as List? ?? [];
    return list.map((e) => TicketModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<TicketModel> getTicket(int id) async {
    final data = await _client.get('${ApiConstants.tickets}$id/') as Map<String, dynamic>;
    return TicketModel.fromJson(data);
  }

  Future<TicketModel> createTicket({
    required String title,
    required double amount,
    required String category,
    required DateTime date,
    String? description,
    File? mediaFile,
  }) async {
    final body = <String, dynamic>{
      'title': title,
      'amount': amount,
      'category': category,
      'date': date.toIso8601String().split('T').first,
      if (description != null && description.isNotEmpty) 'description': description,
    };
    // For now, create ticket without file; multipart upload handled separately
    final data = await _client.post(ApiConstants.tickets, body: body) as Map<String, dynamic>;
    return TicketModel.fromJson(data);
  }

  Future<TicketModel> reviewTicket({
    required int ticketId,
    required String status,
    String? reviewNote,
  }) async {
    final data = await _client.patch(
      '${ApiConstants.tickets}$ticketId/',
      body: {
        'status': status,
        if (reviewNote != null && reviewNote.isNotEmpty) 'review_note': reviewNote,
        'reviewed_at': DateTime.now().toIso8601String(),
      },
    ) as Map<String, dynamic>;
    return TicketModel.fromJson(data);
  }
}
