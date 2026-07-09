import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import 'package:intl_phone_field/intl_phone_field.dart';
import '../../core/api/api_client.dart';

class AddClientBottomSheet extends ConsumerStatefulWidget {
  const AddClientBottomSheet({super.key});

  @override
  ConsumerState<AddClientBottomSheet> createState() => _AddClientBottomSheetState();
}

class _AddClientBottomSheetState extends ConsumerState<AddClientBottomSheet> {
  final _nameController = TextEditingController();
  final _phoneController = TextEditingController();
  String _fullPhone = '';
  bool _isLoading = false;

  Future<void> _addManualClient() async {
    if (_nameController.text.trim().isEmpty || _phoneController.text.trim().isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Veuillez remplir tous les champs')));
      return;
    }

    setState(() => _isLoading = true);
    try {
      await apiClient.post('/clients/add', data: {
        'nom': _nameController.text.trim(),
        'numero': _fullPhone,
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Client ajouté avec succès')));
      Navigator.pop(context, true);
    } on DioException catch (e) {
      if (!mounted) return;
      String errorMessage = "Erreur de connexion";
      if (e.response?.data != null && e.response?.data is Map) {
        errorMessage = e.response!.data['error'] ?? e.message;
      }
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(errorMessage),
        backgroundColor: Colors.red,
      ));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text('Erreur: $e'),
        backgroundColor: Colors.red,
      ));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _importCSV() async {
    // Fonctionnalité désactivée temporairement pour la V1
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('L\'importation CSV sera bientôt disponible dans une prochaine mise à jour !')));
    
    /*
    try {
      // Le package file_picker a été supprimé pour éviter des erreurs de compilation Gradle
      // FilePickerResult? result = await FilePicker.platform.pickFiles(
      //   type: FileType.custom,
      //   allowedExtensions: ['csv'],
      // );
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Erreur d\'importation: $e')));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
    */
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.only(
        bottom: MediaQuery.of(context).viewInsets.bottom,
        left: 20, right: 20, top: 20,
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          const Text('Ajouter un client', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 20),
          TextField(
            controller: _nameController,
            decoration: const InputDecoration(labelText: 'Nom complet', border: OutlineInputBorder()),
          ),
          const SizedBox(height: 12),
          IntlPhoneField(
            controller: _phoneController,
            decoration: const InputDecoration(
              labelText: 'Numéro WhatsApp',
              border: OutlineInputBorder(),
            ),
            initialCountryCode: 'TG',
            onChanged: (phone) {
              _fullPhone = phone.completeNumber;
            },
          ),
          const SizedBox(height: 20),
          ElevatedButton(
            onPressed: _isLoading ? null : _addManualClient,
            child: _isLoading ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('Ajouter manuellement'),
          ),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 10),
            child: Text('OU', textAlign: TextAlign.center, style: TextStyle(color: Colors.grey)),
          ),
          OutlinedButton.icon(
            onPressed: () => _importCSV(), // Appel à la fonction qui affiche le message "Bientôt disponible"
            icon: const Icon(Icons.attach_file, color: Colors.grey),
            label: const Text('Importer un fichier CSV (Bientôt)', style: TextStyle(color: Colors.grey)),
          ),
          const SizedBox(height: 20),
        ],
      ),
    );
  }
}
