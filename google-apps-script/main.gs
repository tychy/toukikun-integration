function toukikun() {
  /* 定数の定義 */
  const targetCell = 'C4' // アクティブシートのC4セルの値を法人番号として取得
  const outputSheetName = '実行結果';
  const apiKey = 'XXXX'

  /* ここまで */

  var inputSheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
  var outputSheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(outputSheetName);
  if (!outputSheet) {
    Browser.msgBox("出力シートが見つかりません: " + outputSheetName);
    return; // シートが存在しない場合は終了
  }

  var houjinNumber = inputSheet.getRange(targetCell).getValue();
  var url = 'https://api.tychy.jp/v1/toukikun/' + houjinNumber;

  var headers = {
    'Authorization': 'Bearer ' + apiKey
  };

  var options = {
    'headers': headers,
    'muteHttpExceptions': true  // 失敗した場合でもレスポンスを取得
  };

  const maxRetries = 3;  // 最大リトライ回数
  const retryDelay = 5000;  // リトライ間隔（ミリ秒）
  var attempts = 0;
  var success = false;

  while (attempts < maxRetries && !success) {
    attempts++;
    var response = UrlFetchApp.fetch(url, options);
    var statusCode = response.getResponseCode();
    
    if (statusCode === 504 || statusCode === 202) {
      Logger.log(statusCode+"エラーが発生しました。リトライします... (" + attempts + "/" + maxRetries + ")");
      Utilities.sleep(retryDelay);  // リトライ前にSleep
    } else if (statusCode === 200) {
      var content = response.getContentText();
      var data = JSON.parse(content);
  
      Logger.log("法人名: " + data.houjin_name + "\n法人番号: " + data.houjin_number);
      var currentDate = new Date();
      
      // データをスプレッドシートに書き込む
      outputSheet.appendRow([
        currentDate,
        data.request_id,                   // リクエストID
        data.is_charged,                   // 課金されたか
        data.houjin_number,                // 法人番号
        data.houjin_name,                  // 法人名
        data.houjin_address,               // 法人住所
        data.houjin_capital,               // 資本金
        data.houjin_stock,                 // 株式数
        data.houjin_executive_names.join(', '), // 役員名 (配列なので結合)
        data.houjin_representative_names.join(', '), // 代表者名 (配列なので結合)
        data.houjin_created_at,
        data.houjin_bankrupted_at,
        data.houjin_dissolved_at,
        data.houjin_continued_at,
        data.file_id,                      // ファイルID (/v1/getpdf/ファイルIDとして利用)
        data.signed_url                    // PDFへの署名付きURL
      ]);

      Browser.msgBox("データがスプレッドシートに書き込まれました。");
      success = true;  // リクエストが成功したのでループを抜ける
    } else {
      // 504以外のエラーコードに対応
      var errorMsg = "エラー: " + statusCode + "\nレスポンス: " + response.getContentText();
      Browser.msgBox(errorMsg);
      outputSheet.appendRow([new Date(), "エラー", errorMsg]);
      break;
    }
  }

  if (!success) {
    Browser.msgBox("最大リトライ回数に達しました。リクエストは成功しませんでした。");
  }
}
