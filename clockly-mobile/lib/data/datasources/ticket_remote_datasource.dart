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
      if (status != null) 'status': status,
      if (from != null) 'from_date': from.toIso8601String().split('T').first,
      if (to != null) 'to_date': to.toIso8601String().split('T').first,
    };
    final data = await _client.get(ApiConstants.tickets, queryParams: params);
    // Backend returns {"items": [...]}
    final list = data is List ? data : (data as Map<String, dynamic>)['items'] as List? ?? [];
    return list.map((e) => TicketModel.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<TicketModel> getTicket(int id) async {
    final data = await _client.get('${ApiConstants.tickets}/$id') as Map<String, dynamic>;
    // Backend returns {"ticket": {...}}
    final ticket = data['ticket'] as Map<String, dynamic>? ?? data;
    return TicketModel.fromJson(ticket);
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
    final data = await _client.post(ApiConstants.tickets, body: body) as Map<String, dynamic>;
    // Backend returns {"ticket": {...}}
    final ticket = data['ticket'] as Map<String, dynamic>? ?? data;
    return TicketModel.fromJson(ticket);
  }

  Future<TicketModel> reviewTicket({
    required int ticketId,
    required String status,
    String? reviewNote,
  }) async {
    final data = await _client.patch(
      '${ApiConstants.tickets}/$ticketId',
      body: {
        'status': status,
        if (reviewNote != null && reviewNote.isNotEmpty) 'review_note': reviewNote,
      },
    ) as Map<String, dynamic>;
    // Backend returns {"ticket": {...}}
    final ticket = data['ticket'] as Map<String, dynamic>? ?? data;
    return TicketModel.fromJson(ticket);
  }
}
